import chess
from flask import jsonify, request, session
from flask_login import current_user, login_required

from app.models import Game
from app.services.chess_helpers import (
    board_to_svg_data,
    clear_session_game_state,
    get_board_from_session,
    get_stockfish_hint,
    save_board_to_session,
)
from app.services.game_storage import create_saved_game


def register_game_api_routes(app):
    @app.route("/api/game/new", methods=["POST"])
    @login_required
    def api_new_game():
        data = request.get_json() or {}
        opponent = data.get("opponent", "Stockfish")
        color = data.get("color", "white")

        board = chess.Board()
        session["game_fen"] = board.fen()
        session["game_moves"] = []
        session["game_fens"] = [board.fen()]
        session["game_opponent"] = opponent
        session["game_color"] = color
        session["game_active"] = True

        return jsonify(
            {
                "success": True,
                "fen": board.fen(),
                "svg": board_to_svg_data(board),
                "turn": "White",
                "move_count": 0,
                "is_check": False,
                "is_game_over": False,
                "message": "New game started. White to move.",
            }
        )

    @app.route("/api/game/move", methods=["POST"])
    @login_required
    def api_make_move():
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
        response = {
            "success": True,
            "move": san,
            "fen": board.fen(),
            "svg": board_to_svg_data(board, last_move=move),
            "turn": turn,
            "move_count": len(moves_list),
            "moves_list": moves_list,
            "is_check": board.is_check(),
            "is_game_over": board.is_game_over(),
            "message": "",
        }

        if board.is_game_over():
            outcome = board.outcome()
            if outcome and outcome.winner is not None:
                winner = "White" if outcome.winner == chess.WHITE else "Black"
                response["message"] = f"Checkmate! {winner} wins!"
                response["result"] = "1-0" if outcome.winner == chess.WHITE else "0-1"
            elif board.is_stalemate():
                response["message"] = "Stalemate. Draw."
                response["result"] = "1/2-1/2"
            elif board.is_insufficient_material():
                response["message"] = "Draw by insufficient material."
                response["result"] = "1/2-1/2"
            elif board.is_seventyfive_moves():
                response["message"] = "Draw by 75-move rule."
                response["result"] = "1/2-1/2"
            elif board.is_fivefold_repetition():
                response["message"] = "Draw by fivefold repetition."
                response["result"] = "1/2-1/2"
            else:
                response["message"] = "Game over. Draw."
                response["result"] = "1/2-1/2"
            session["game_active"] = False
        elif board.is_check():
            response["message"] = f"Check! {turn} to move."

        return jsonify(response)

    @app.route("/api/game/hint", methods=["GET"])
    @login_required
    def api_get_hint():
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
        board = get_board_from_session()
        if board is None:
            return jsonify({"success": False, "active": False}), 200

        turn = "White" if board.turn == chess.WHITE else "Black"
        return jsonify(
            {
                "success": True,
                "active": session.get("game_active", False),
                "fen": board.fen(),
                "svg": board_to_svg_data(board),
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
