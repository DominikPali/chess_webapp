from datetime import datetime, timezone

import chess
from flask import jsonify, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import ActiveGame, User
from app.services.chess_helpers import (
    board_to_svg_data,
    cleanup_expired_rooms,
    generate_game_code,
    is_room_expired,
)
from app.services.game_storage import create_saved_game


def _expired_response():
    return (
        jsonify(
            {
                "success": False,
                "error": "Game expired due to inactivity.",
                "expired": True,
            }
        ),
        410,
    )


def _orientation_for(my_color):
    return chess.BLACK if my_color == "black" else chess.WHITE


def register_room_api_routes(app):
    @app.route("/api/room/create", methods=["POST"])
    @login_required
    def api_create_room():
        color = (request.get_json() or {}).get("color", "white")
        room = ActiveGame(code=generate_game_code(), status="waiting")

        if color == "white":
            room.white_user_id = current_user.id
        else:
            room.black_user_id = current_user.id

        room.fen = chess.STARTING_FEN
        room.set_moves([])
        room.set_fens([chess.STARTING_FEN])

        db.session.add(room)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "code": room.code,
                "color": color,
                "message": f"Room created! Share code: {room.code}",
            }
        )

    @app.route("/api/room/join", methods=["POST"])
    @login_required
    def api_join_room():
        cleanup_expired_rooms()
        code = (request.get_json() or {}).get("code", "").strip().upper()
        if not code:
            return jsonify({"success": False, "error": "No game code provided."}), 400

        room = ActiveGame.query.filter_by(code=code).first()
        if not room:
            return jsonify({"success": False, "error": "Game not found. Check the code."}), 404
        if room.status != "waiting":
            return jsonify(
                {"success": False, "error": "This game is no longer available."}
            ), 400
        if room.white_user_id == current_user.id or room.black_user_id == current_user.id:
            return jsonify({"success": False, "error": "You are already in this game."}), 400

        if room.white_user_id is None:
            room.white_user_id = current_user.id
            my_color = "white"
        elif room.black_user_id is None:
            room.black_user_id = current_user.id
            my_color = "black"
        else:
            return jsonify({"success": False, "error": "This game is already full."}), 400

        room.status = "active"
        room.activated_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "code": code,
                "color": my_color,
                "message": "Joined the game!",
            }
        )

    @app.route("/api/room/state/<code>", methods=["GET"])
    @login_required
    def api_room_state(code):
        room = ActiveGame.query.filter_by(code=code.upper()).first()
        if not room:
            return jsonify({"success": False, "error": "Room not found."}), 404

        if is_room_expired(room):
            db.session.delete(room)
            db.session.commit()
            return _expired_response()

        if room.white_user_id == current_user.id:
            my_color = "white"
            opponent_user = db.session.get(User, room.black_user_id) if room.black_user_id else None
        elif room.black_user_id == current_user.id:
            my_color = "black"
            opponent_user = db.session.get(User, room.white_user_id) if room.white_user_id else None
        else:
            return jsonify({"success": False, "error": "You are not in this game."}), 403

        board = chess.Board(room.fen)
        turn = "white" if board.turn == chess.WHITE else "black"
        moves_list = room.get_moves()

        return jsonify(
            {
                "success": True,
                "status": room.status,
                "fen": room.fen,
                "svg": board_to_svg_data(board, orientation=_orientation_for(my_color)),
                "turn": turn.capitalize(),
                "is_my_turn": turn == my_color,
                "my_color": my_color,
                "opponent": opponent_user.username if opponent_user else "Waiting...",
                "move_count": len(moves_list),
                "moves_list": moves_list,
                "is_check": board.is_check(),
                "is_game_over": board.is_game_over(),
                "result": room.result,
            }
        )

    @app.route("/api/room/move/<code>", methods=["POST"])
    @login_required
    def api_room_move(code):
        room = ActiveGame.query.filter_by(code=code.upper()).first()
        if not room:
            return jsonify({"success": False, "error": "Room not found."}), 404
        if is_room_expired(room):
            db.session.delete(room)
            db.session.commit()
            return _expired_response()
        if room.status != "active":
            return jsonify({"success": False, "error": "Game is not active."}), 400

        board = chess.Board(room.fen)
        turn_color = "white" if board.turn == chess.WHITE else "black"

        if turn_color == "white" and room.white_user_id != current_user.id:
            return jsonify({"success": False, "error": "It's not your turn."}), 400
        if turn_color == "black" and room.black_user_id != current_user.id:
            return jsonify({"success": False, "error": "It's not your turn."}), 400

        my_color = "white" if room.white_user_id == current_user.id else "black"

        move_san = (request.get_json() or {}).get("move", "").strip()
        if not move_san:
            return jsonify({"success": False, "error": "No move provided."}), 400

        try:
            move = board.parse_san(move_san)
        except chess.InvalidMoveError:
            return jsonify({"success": False, "error": f"Invalid notation: '{move_san}'"}), 400
        except chess.IllegalMoveError:
            return jsonify({"success": False, "error": f"Illegal move: '{move_san}'"}), 400
        except chess.AmbiguousMoveError:
            return jsonify({"success": False, "error": f"Ambiguous move: '{move_san}'"}), 400

        if move not in board.legal_moves:
            return jsonify({"success": False, "error": f"Illegal move: '{move_san}'"}), 400

        san = board.san(move)
        board.push(move)

        moves_list = room.get_moves()
        moves_list.append(san)
        room.set_moves(moves_list)

        fens_list = room.get_fens()
        fens_list.append(board.fen())
        room.set_fens(fens_list)
        room.fen = board.fen()

        result_str = None
        message = ""
        if board.is_game_over():
            outcome = board.outcome()
            if outcome and outcome.winner is not None:
                winner = "White" if outcome.winner == chess.WHITE else "Black"
                message = f"Checkmate! {winner} wins!"
                result_str = "1-0" if outcome.winner == chess.WHITE else "0-1"
            else:
                message = "Draw."
                result_str = "1/2-1/2"
            room.status = "finished"
            room.result = result_str
        elif board.is_check():
            next_turn = "White" if board.turn == chess.WHITE else "Black"
            message = f"Check! {next_turn} to move."

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "move": san,
                "fen": board.fen(),
                "svg": board_to_svg_data(board, last_move=move, orientation=_orientation_for(my_color)),
                "turn": "White" if board.turn == chess.WHITE else "Black",
                "move_count": len(moves_list),
                "moves_list": moves_list,
                "is_check": board.is_check(),
                "is_game_over": board.is_game_over(),
                "result": result_str,
                "message": message,
            }
        )

    @app.route("/api/room/resign/<code>", methods=["POST"])
    @login_required
    def api_room_resign(code):
        room = ActiveGame.query.filter_by(code=code.upper()).first()
        if not room:
            return jsonify({"success": False, "error": "Room not found."}), 404

        if room.white_user_id == current_user.id:
            my_color = "white"
        elif room.black_user_id == current_user.id:
            my_color = "black"
        else:
            return jsonify({"success": False, "error": "You are not in this game."}), 403

        result = "0-1" if my_color == "white" else "1-0"
        winner = "Black" if my_color == "white" else "White"
        room.status = "finished"
        room.result = result
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "result": result,
                "message": f"{my_color.capitalize()} resigned. {winner} wins!",
            }
        )

    @app.route("/api/room/save/<code>", methods=["POST"])
    @login_required
    def api_room_save(code):
        room = ActiveGame.query.filter_by(code=code.upper()).first()
        if not room:
            return jsonify({"success": False, "error": "Room not found."}), 404

        if room.white_user_id == current_user.id:
            my_color = "white"
            opponent_user = db.session.get(User, room.black_user_id) if room.black_user_id else None
        elif room.black_user_id == current_user.id:
            my_color = "black"
            opponent_user = db.session.get(User, room.white_user_id) if room.white_user_id else None
        else:
            return jsonify({"success": False, "error": "You are not in this game."}), 403

        moves_list = room.get_moves()
        if not moves_list:
            return jsonify({"success": False, "error": "No moves to save."}), 400

        opponent_name = opponent_user.username if opponent_user else "Unknown"
        result = room.result or "1/2-1/2"
        white_name = current_user.username if my_color == "white" else opponent_name
        black_name = opponent_name if my_color == "white" else current_user.username
        game = create_saved_game(
            user_id=current_user.id,
            opponent=opponent_name,
            color=my_color,
            result=result,
            moves_list=moves_list,
            white_name=white_name,
            black_name=black_name,
        )

        return jsonify(
            {
                "success": True,
                "game_id": game.id,
                "message": "Game saved successfully!",
            }
        )
