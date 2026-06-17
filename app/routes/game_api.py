"""Single-player game JSON API — start games, validate moves, drive the Stockfish bot, hints, resign, and save."""

import chess
from flask import jsonify, request, session
from flask_login import current_user, login_required

from app.models import Game
from app.services.chess_helpers import (
    board_to_svg_data,
    clear_session_game_state,
    get_board_from_session,
    get_stockfish_hint,
    get_stockfish_move,
    save_board_to_session,
    session_orientation,
)
from app.services.game_storage import create_saved_game


def _outcome_message(board):
    """Return (message, result) tuple for a finished board, or (None, None)."""
    if not board.is_game_over():
        return None, None
    outcome = board.outcome()
    if outcome and outcome.winner is not None:
        winner = "White" if outcome.winner == chess.WHITE else "Black"
        result = "1-0" if outcome.winner == chess.WHITE else "0-1"
        return f"Checkmate! {winner} wins!", result
    if board.is_stalemate():
        return "Stalemate. Draw.", "1/2-1/2"
    if board.is_insufficient_material():
        return "Draw by insufficient material.", "1/2-1/2"
    if board.is_seventyfive_moves():
        return "Draw by 75-move rule.", "1/2-1/2"
    if board.is_fivefold_repetition():
        return "Draw by fivefold repetition.", "1/2-1/2"
    return "Game over. Draw.", "1/2-1/2"


def _apply_bot_move(board):
    """If opponent is Stockfish, play a bot move on the board. Returns dict with bot info or error."""
    if session.get("game_opponent") != "Stockfish":
        return None
    if board.is_game_over():
        return None

    elo = session.get("game_bot_elo", 1500)
    bot = get_stockfish_move(board, elo)
    if bot is None:
        return {
            "error": "Bot unavailable — install Stockfish (brew install stockfish).",
        }

    san = bot["san"]
    move_obj = bot["move_obj"]
    board.push(move_obj)
    save_board_to_session(board)

    moves_list = session.get("game_moves", [])
    moves_list.append(san)
    session["game_moves"] = moves_list

    fens_list = session.get("game_fens", [])
    fens_list.append(board.fen())
    session["game_fens"] = fens_list

    return {"san": san, "move_obj": move_obj}


def register_game_api_routes(app):
    """Register all single-player game JSON API endpoints on the Flask app."""
    @app.route("/api/game/new", methods=["POST"])
    @login_required
    def api_new_game():
        """Initialise a fresh game in the session from the posted opponent/color/ELO and return the start state."""
        data = request.get_json() or {}
        opponent = data.get("opponent", "Stockfish")
        color = data.get("color", "white")
        try:
            bot_elo = int(data.get("bot_elo", 1500))
        except (TypeError, ValueError):
            bot_elo = 1500
        bot_elo = max(600, min(2800, bot_elo))

        board = chess.Board()
        session["game_fen"] = board.fen()
        session["game_moves"] = []
        session["game_fens"] = [board.fen()]
        session["game_opponent"] = opponent
        session["game_color"] = color
        session["game_active"] = True
        session["game_bot_elo"] = bot_elo

        bot_pending = opponent == "Stockfish" and color == "black"

        return jsonify(
            {
                "success": True,
                "fen": board.fen(),
                "svg": board_to_svg_data(board, orientation=session_orientation()),
                "turn": "White",
                "move_count": 0,
                "moves_list": [],
                "is_check": False,
                "is_game_over": False,
                "message": "New game started. White to move.",
                "bot_pending": bot_pending,
            }
        )

    @app.route("/api/game/move", methods=["POST"])
    @login_required
    def api_make_move():
        """Parse and validate the player's SAN move, push it to the session board, and return the updated state."""
        board = get_board_from_session()
        if board is None:
            return jsonify(
                {"success": False, "error": "No active game. Start a new game first."}
            ), 400

        move_san = (request.get_json() or {}).get("move", "").strip()
        if not move_san:
            return jsonify({"success": False, "error": "No move provided."}), 400

        try:
            move = board.parse_san(move_san)
        except chess.InvalidMoveError:
            return jsonify(
                {"success": False, "error": f"Invalid notation syntax: '{move_san}'"}
            ), 400
        except chess.IllegalMoveError:
            return jsonify({"success": False, "error": f"Illegal move: '{move_san}'"}), 400
        except chess.AmbiguousMoveError:
            return jsonify(
                {
                    "success": False,
                    "error": f"Ambiguous move: '{move_san}'. Be more specific.",
                }
            ), 400

        if move not in board.legal_moves:
            return jsonify({"success": False, "error": f"Illegal move: '{move_san}'"}), 400

        san = board.san(move)
        board.push(move)
        save_board_to_session(board)

        moves_list = session.get("game_moves", [])
        moves_list.append(san)
        session["game_moves"] = moves_list

        fens_list = session.get("game_fens", [])
        fens_list.append(board.fen())
        session["game_fens"] = fens_list

        turn = "White" if board.turn == chess.WHITE else "Black"
        bot_pending = (
            session.get("game_opponent") == "Stockfish"
            and not board.is_game_over()
        )
        response = {
            "success": True,
            "move": san,
            "fen": board.fen(),
            "svg": board_to_svg_data(
                board, last_move=move, orientation=session_orientation()
            ),
            "turn": turn,
            "move_count": len(session.get("game_moves", [])),
            "moves_list": session.get("game_moves", []),
            "is_check": board.is_check(),
            "is_game_over": board.is_game_over(),
            "message": "",
            "bot_pending": bot_pending,
        }

        message, result = _outcome_message(board)
        if message:
            response["message"] = message
            response["result"] = result
            session["game_active"] = False
        elif board.is_check():
            response["message"] = f"Check! {turn} to move."

        return jsonify(response)

    @app.route("/api/game/bot-move", methods=["POST"])
    @login_required
    def api_bot_move():
        """Have the Stockfish opponent compute and play its reply, returning the new board state or an error."""
        board = get_board_from_session()
        if board is None:
            return jsonify({"success": False, "error": "No active game."}), 400
        if board.is_game_over():
            return jsonify({"success": False, "error": "Game is over."}), 400
        if session.get("game_opponent") != "Stockfish":
            return jsonify({"success": False, "error": "Opponent is not the bot."}), 400

        bot = _apply_bot_move(board)
        if bot is None or "error" in (bot or {}):
            return jsonify(
                {
                    "success": False,
                    "error": (bot or {}).get(
                        "error", "Bot unavailable."
                    ),
                }
            ), 503

        turn = "White" if board.turn == chess.WHITE else "Black"
        response = {
            "success": True,
            "bot_move": bot["san"],
            "fen": board.fen(),
            "svg": board_to_svg_data(
                board, last_move=bot["move_obj"], orientation=session_orientation()
            ),
            "turn": turn,
            "move_count": len(session.get("game_moves", [])),
            "moves_list": session.get("game_moves", []),
            "is_check": board.is_check(),
            "is_game_over": board.is_game_over(),
            "message": f"Bot played {bot['san']}.",
        }

        message, result = _outcome_message(board)
        if message:
            response["message"] = message
            response["result"] = result
            session["game_active"] = False
        elif board.is_check():
            response["message"] = f"Check! {turn} to move."

        return jsonify(response)

    @app.route("/api/game/hint", methods=["GET"])
    @login_required
    def api_get_hint():
        """Return Stockfish's best move and position evaluation for the current session position."""
        board = get_board_from_session()
        if board is None:
            return jsonify({"success": False, "error": "No active game."}), 400

        if board.is_game_over():
            return jsonify({"success": False, "error": "Game is already over."}), 400

        hint = get_stockfish_hint(board)
        if hint:
            return jsonify(
                {
                    "success": True,
                    "hint_move": hint["move"],
                    "evaluation": hint["evaluation"],
                    "score_norm": hint["score_norm"],
                    "mate_in": hint["mate_in"],
                }
            )

        return jsonify(
            {
                "success": False,
                "error": "Stockfish is not available. Install it and set STOCKFISH_PATH.",
            }
        ), 503

    @app.route("/api/game/state", methods=["GET"])
    @login_required
    def api_game_state():
        """Return the current in-progress game's full state from the session, used to resume after a page reload."""
        board = get_board_from_session()
        if board is None:
            return jsonify({"success": False, "active": False}), 200

        turn = "White" if board.turn == chess.WHITE else "Black"
        return jsonify(
            {
                "success": True,
                "active": session.get("game_active", False),
                "fen": board.fen(),
                "svg": board_to_svg_data(board, orientation=session_orientation()),
                "turn": turn,
                "move_count": len(session.get("game_moves", [])),
                "moves_list": session.get("game_moves", []),
                "is_check": board.is_check(),
                "is_game_over": board.is_game_over(),
                "opponent": session.get("game_opponent", ""),
                "color": session.get("game_color", "white"),
            }
        )

    @app.route("/api/game/resign", methods=["POST"])
    @login_required
    def api_resign():
        """Mark the current game inactive and return the result awarding the win to the opponent's color."""
        if get_board_from_session() is None:
            return jsonify({"success": False, "error": "No active game."}), 400

        color = session.get("game_color", "white")
        result = "0-1" if color == "white" else "1-0"
        winner = "Black" if color == "white" else "White"
        session["game_active"] = False

        return jsonify(
            {
                "success": True,
                "result": result,
                "message": f"{color.capitalize()} resigned. {winner} wins!",
            }
        )

    @app.route("/api/game/save", methods=["POST"])
    @login_required
    def api_save_game():
        """Persist the finished session game (moves, PGN, result) to the database and clear the session state."""
        data = request.get_json() or {}
        result = data.get("result", "1/2-1/2")
        moves_list = session.get("game_moves", [])
        opponent = session.get("game_opponent", "Unknown")
        color = session.get("game_color", "white")

        if not moves_list:
            return jsonify({"success": False, "error": "No moves to save."}), 400

        white_name = current_user.username if color == "white" else opponent
        black_name = opponent if color == "white" else current_user.username
        game = create_saved_game(
            user_id=current_user.id,
            opponent=opponent,
            color=color,
            result=result,
            moves_list=moves_list,
            white_name=white_name,
            black_name=black_name,
        )
        clear_session_game_state()

        return jsonify(
            {
                "success": True,
                "game_id": game.id,
                "message": "Game saved successfully!",
            }
        )
