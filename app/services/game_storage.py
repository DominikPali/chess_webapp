"""Game persistence service — turns a finished move list into saved Game/Move records and updates the user's stats."""

from datetime import datetime

import chess
import chess.pgn

from app.extensions import db
from app.models import Game, Move, User

DRAW_RESULTS = ("1/2-1/2", "½-½")


def _result_for_user(color, result):
    """Classify a finished game from the saving user's perspective."""
    if result in DRAW_RESULTS:
        return "draw"
    if (color == "white" and result == "1-0") or (color == "black" and result == "0-1"):
        return "win"
    return "loss"


def create_saved_game(user_id, opponent, color, result, moves_list, white_name, black_name):
    """Build a Game (with PGN), replay the moves into Move rows, bump the user's win/draw/loss count, and commit."""
    board = chess.Board()
    pgn_game = chess.pgn.Game()
    pgn_game.headers["White"] = white_name
    pgn_game.headers["Black"] = black_name
    pgn_game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
    pgn_game.headers["Result"] = result

    node = pgn_game
    for san in moves_list:
        move = board.parse_san(san)
        node = node.add_variation(move)
        board.push(move)

    game = Game(
        user_id=user_id,
        opponent=opponent,
        color=color,
        result=result,
        moves=len(moves_list),
        pgn=str(pgn_game),
        fen_final=board.fen(),
    )
    db.session.add(game)
    db.session.flush()

    replay_board = chess.Board()
    for index, san in enumerate(moves_list):
        move_obj = replay_board.parse_san(san)
        replay_board.push(move_obj)
        db.session.add(
            Move(
                game_id=game.id,
                move_number=index + 1,
                color="white" if index % 2 == 0 else "black",
                notation=san,
                fen_after=replay_board.fen(),
            )
        )

    user = db.session.get(User, user_id)
    if user is not None:
        outcome = _result_for_user(color, result)
        if outcome == "win":
            user.wins = (user.wins or 0) + 1
        elif outcome == "draw":
            user.draws = (user.draws or 0) + 1
        else:
            user.losses = (user.losses or 0) + 1

    db.session.commit()
    return game
