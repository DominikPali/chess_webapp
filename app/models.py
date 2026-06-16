import json
from datetime import datetime, timezone

import chess
from flask_login import UserMixin

from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    wins = db.Column(db.Integer, nullable=False, default=0)
    draws = db.Column(db.Integer, nullable=False, default=0)
    losses = db.Column(db.Integer, nullable=False, default=0)
    games = db.relationship(
        "Game",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )


class Game(db.Model):
    __tablename__ = "game"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date_played = db.Column(
        db.Date,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).date(),
    )
    opponent = db.Column(db.String(80), nullable=False)
    color = db.Column(db.String(5), nullable=False)
    result = db.Column(db.String(10), nullable=False)
    moves = db.Column(db.Integer, nullable=False, default=0)
    pgn = db.Column(db.Text, nullable=True)
    fen_final = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    move_records = db.relationship(
        "Move",
        backref="game",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="Move.move_number",
    )


class Move(db.Model):
    __tablename__ = "move"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False)
    move_number = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(5), nullable=False)
    notation = db.Column(db.String(10), nullable=False)
    fen_after = db.Column(db.String(100), nullable=False)


class ActiveGame(db.Model):
    __tablename__ = "active_game"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), unique=True, nullable=False, index=True)
    white_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    black_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    fen = db.Column(db.String(100), nullable=False, default=chess.STARTING_FEN)
    moves_json = db.Column(db.Text, nullable=False, default="[]")
    fens_json = db.Column(db.Text, nullable=False, default="[]")
    status = db.Column(db.String(20), nullable=False, default="waiting")
    result = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    activated_at = db.Column(db.DateTime, nullable=True)

    white_user = db.relationship("User", foreign_keys=[white_user_id])
    black_user = db.relationship("User", foreign_keys=[black_user_id])

    def get_moves(self):
        return json.loads(self.moves_json or "[]")

    def set_moves(self, moves_list):
        self.moves_json = json.dumps(moves_list)

    def get_fens(self):
        return json.loads(self.fens_json or "[]")

    def set_fens(self, fens_list):
        self.fens_json = json.dumps(fens_list)
