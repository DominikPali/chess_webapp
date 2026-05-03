import os
import random
import string

import chess
import chess.engine
import chess.svg
from flask import current_app, session

from app.models import ActiveGame

SESSION_GAME_KEYS = (
    "game_fen",
    "game_moves",
    "game_fens",
    "game_opponent",
    "game_color",
    "game_active",
)


def generate_game_code():
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(chars, k=6))
        if not ActiveGame.query.filter_by(code=code).first():
            return code


def get_board_from_session():
    fen = session.get("game_fen")
    return chess.Board(fen) if fen else None


def save_board_to_session(board):
    session["game_fen"] = board.fen()


def clear_session_game_state():
    for key in SESSION_GAME_KEYS:
        session.pop(key, None)


def get_stockfish_hint(board, time_limit=0.5):
    stockfish_path = current_app.config.get("STOCKFISH_PATH", "")
    if not stockfish_path or not os.path.exists(stockfish_path):
        return None

    try:
        with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
            result = engine.analyse(board, chess.engine.Limit(time=time_limit))
            best_move = result.get("pv", [None])[0]
            score = result.get("score")
            if best_move:
                evaluation = ""
                if score:
                    pov = score.white()
                    if pov.is_mate():
                        evaluation = f"Mate in {pov.mate()}"
                    else:
                        evaluation = f"{pov.score() / 100.0:+.1f}"
                return {"move": board.san(best_move), "evaluation": evaluation}
    except Exception:
        return None

    return None


def board_to_svg_data(board, last_move=None):
    kwargs = {"size": 400}
    if last_move:
        kwargs["lastmove"] = last_move
    if board.is_check():
        kwargs["check"] = board.king(board.turn)
    return chess.svg.board(board, **kwargs)
