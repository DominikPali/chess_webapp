import os
import random
import string
from datetime import datetime, timedelta, timezone

import chess
import chess.engine
import chess.svg
from flask import current_app, session

from app.extensions import db
from app.models import ActiveGame

WAITING_TTL = timedelta(days=1)
ACTIVE_TTL = timedelta(hours=12)

SESSION_GAME_KEYS = (
    "game_fen",
    "game_moves",
    "game_fens",
    "game_opponent",
    "game_color",
    "game_active",
    "game_bot_elo",
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


def get_stockfish_move(board, elo):
    stockfish_path = current_app.config.get("STOCKFISH_PATH", "")
    if not stockfish_path or not os.path.exists(stockfish_path):
        return None

    try:
        elo = int(elo)
    except (TypeError, ValueError):
        elo = 1500
    elo = max(600, min(2800, elo))

    try:
        with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
            if elo >= 1320:
                engine.configure({"UCI_LimitStrength": True, "UCI_Elo": elo})
                limit = chess.engine.Limit(time=0.5)
            else:
                frac = (elo - 600) / (1320 - 600)
                skill = int(frac * 10)
                depth = max(1, int(1 + frac * 7))
                time_budget = 0.05 + frac * 0.25
                engine.configure(
                    {"UCI_LimitStrength": False, "Skill Level": skill}
                )
                limit = chess.engine.Limit(depth=depth, time=time_budget)
            result = engine.play(board, limit)
            if result.move is not None and result.move in board.legal_moves:
                return {"move_obj": result.move, "san": board.san(result.move)}
    except Exception:
        return None

    return None


def board_to_svg_data(board, last_move=None, orientation=chess.WHITE):
    kwargs = {"size": 400, "orientation": orientation}
    if last_move:
        kwargs["lastmove"] = last_move
    if board.is_check():
        kwargs["check"] = board.king(board.turn)
    return chess.svg.board(board, **kwargs)


def session_orientation():
    return chess.BLACK if session.get("game_color") == "black" else chess.WHITE


def _ensure_utc(dt):
    """SQLite returns naive datetimes; treat them as UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def is_room_expired(room):
    """True if the room's code/game has outlived its TTL."""
    now = datetime.now(timezone.utc)
    if room.status == "waiting":
        created = _ensure_utc(room.created_at)
        return created is not None and created + WAITING_TTL < now
    if room.status == "active":
        anchor = _ensure_utc(room.activated_at) or _ensure_utc(room.created_at)
        return anchor is not None and anchor + ACTIVE_TTL < now
    return False


def cleanup_expired_rooms():
    """Lazy sweep — delete every waiting/active room past its TTL.
    Finished rooms are left to the save flow."""
    rooms = ActiveGame.query.filter(
        ActiveGame.status.in_(("waiting", "active"))
    ).all()
    deleted = 0
    for room in rooms:
        if is_room_expired(room):
            db.session.delete(room)
            deleted += 1
    if deleted:
        db.session.commit()
    return deleted
