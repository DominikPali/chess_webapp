import chess
from flask import jsonify, request
from flask_login import current_user, login_required

from app.models import Game, Move
from app.services.chess_helpers import board_to_svg_data, get_stockfish_hint


def register_analysis_api_routes(app):
    @app.route("/api/analyse/<int:game_id>", methods=["GET"])
    @login_required
    def api_analyse_game(game_id):
        game = Game.query.filter_by(id=game_id, user_id=current_user.id).first_or_404()
        move_records = (
            Move.query.filter_by(game_id=game_id).order_by(Move.move_number).all()
        )
        moves_data = [
            {
                "number": move.move_number,
                "color": move.color,
                "notation": move.notation,
                "fen_after": move.fen_after,
            }
            for move in move_records
        ]

        return jsonify(
            {
                "success": True,
                "game_id": game.id,
                "opponent": game.opponent,
                "color": game.color,
                "result": game.result,
                "date": game.date_played.strftime("%Y-%m-%d"),
                "pgn": game.pgn,
                "total_moves": game.moves,
                "start_fen": chess.STARTING_FEN,
                "start_svg": board_to_svg_data(chess.Board()),
                "moves": moves_data,
            }
        )

    @app.route("/api/analyse/svg", methods=["POST"])
    @login_required
    def api_analyse_svg():
        fen = (request.get_json() or {}).get("fen", chess.STARTING_FEN)
        try:
            board = chess.Board(fen)
        except ValueError:
            return jsonify({"success": False, "error": "Invalid FEN."}), 400

        return jsonify({"success": True, "svg": board_to_svg_data(board)})

    @app.route("/api/analyse/bestmove", methods=["POST"])
    @login_required
    def api_analyse_bestmove():
        fen = (request.get_json() or {}).get("fen", chess.STARTING_FEN)
        try:
            board = chess.Board(fen)
        except ValueError:
            return jsonify({"success": False, "error": "Invalid FEN."}), 400

        if board.is_game_over():
            return jsonify({"success": True, "best_move": None, "evaluation": "Game over"})

        hint = get_stockfish_hint(board, time_limit=1.0)
        if hint:
            return jsonify(
                {
                    "success": True,
                    "best_move": hint["move"],
                    "evaluation": hint["evaluation"],
                }
            )

        return jsonify({"success": False, "error": "Stockfish is not available."}), 503
