import os
import random
from datetime import datetime, timezone

import chess
import chess.engine
import chess.pgn
import chess.svg
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "trimmed-copy-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(base_dir, 'notationlearner.db')}")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    games = db.relationship("Game", backref="user", lazy=True, cascade="all, delete-orphan")


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    opponent = db.Column(db.String(80), nullable=False)
    color = db.Column(db.String(5), nullable=False)
    result = db.Column(db.String(10), nullable=False)
    moves = db.Column(db.Integer, nullable=False, default=0)
    pgn = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()


def clear_game():
    for key in ["game_fen", "game_moves", "game_color", "game_active", "game_result", "game_opponent"]:
        session.pop(key, None)


def get_board():
    fen = session.get("game_fen")
    if not fen:
        return None
    try:
        return chess.Board(fen)
    except ValueError:
        clear_game()
        return None


def save_board(board):
    session["game_fen"] = board.fen()


def find_engine_path():
    options = [
        os.environ.get("STOCKFISH_PATH"),
        "/opt/homebrew/bin/stockfish",
        "/usr/local/bin/stockfish",
        "/usr/bin/stockfish",
    ]
    for option in options:
        if option and os.path.exists(option):
            return option
    return None


ENGINE_PATH = find_engine_path()


def board_svg(board, last_move=None):
    options = {"size": 420}
    if last_move:
        options["lastmove"] = last_move
    if board.is_check():
        options["check"] = board.king(board.turn)
    return chess.svg.board(board, **options)


def player_turn():
    return chess.WHITE if session.get("game_color", "white") == "white" else chess.BLACK


def push_move(board, move):
    san = board.san(move)
    board.push(move)
    moves = list(session.get("game_moves", []))
    moves.append(san)
    session["game_moves"] = moves
    save_board(board)
    return san


def choose_bot_move(board):
    if ENGINE_PATH:
        try:
            with chess.engine.SimpleEngine.popen_uci(ENGINE_PATH) as engine:
                result = engine.play(board, chess.engine.Limit(time=0.2))
                if result.move:
                    return result.move
        except Exception:
            pass
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None
    return random.choice(legal_moves)


def result_for_board(board):
    if not board.is_game_over():
        return None
    outcome = board.outcome()
    if outcome and outcome.winner is not None:
        return "1-0" if outcome.winner == chess.WHITE else "0-1"
    return "1/2-1/2"


def message_for_board(board):
    outcome = board.outcome()
    if outcome and outcome.winner == chess.WHITE:
        return "Checkmate. White wins."
    if outcome and outcome.winner == chess.BLACK:
        return "Checkmate. Black wins."
    if board.is_stalemate():
        return "Draw by stalemate."
    if board.is_insufficient_material():
        return "Draw by insufficient material."
    if board.is_seventyfive_moves():
        return "Draw by the 75-move rule."
    if board.is_fivefold_repetition():
        return "Draw by repetition."
    return "Game over."


def finish_game(board):
    session["game_active"] = False
    session["game_result"] = result_for_board(board)
    return session["game_result"], message_for_board(board)


def game_payload(board, message="", last_move=None):
    turn = "White" if board.turn == chess.WHITE else "Black"
    return {
        "success": True,
        "active": session.get("game_active", False),
        "svg": board_svg(board, last_move),
        "turn": turn,
        "move_count": len(session.get("game_moves", [])),
        "moves_list": session.get("game_moves", []),
        "player_color": session.get("game_color", "white"),
        "is_my_turn": board.turn == player_turn(),
        "is_game_over": board.is_game_over() or not session.get("game_active", False),
        "result": session.get("game_result"),
        "message": message,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("play"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("play"))
        flash("Wrong username or password.", "error")
    return render_template("login.html", mode="login")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("play"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not username or not email or not password:
            flash("Fill in all fields.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        elif User.query.filter_by(username=username).first():
            flash("That username is already taken.", "error")
        elif User.query.filter_by(email=email).first():
            flash("That email is already registered.", "error")
        else:
            user = User(username=username, email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash("Account created. You can log in now.", "success")
            return redirect(url_for("login"))
    return render_template("login.html", mode="register")


@app.route("/logout")
@login_required
def logout():
    clear_game()
    logout_user()
    return redirect(url_for("index"))


@app.route("/play")
@login_required
def play():
    return render_template("play.html")


@app.route("/profile")
@login_required
def profile():
    games = Game.query.filter_by(user_id=current_user.id).order_by(Game.created_at.desc()).all()
    wins = 0
    for game in games:
        if (game.color == "white" and game.result == "1-0") or (game.color == "black" and game.result == "0-1"):
            wins += 1
    return render_template("profile.html", games=games, wins=wins)


@app.route("/api/game/new", methods=["POST"])
@login_required
def api_new_game():
    data = request.get_json() or {}
    color = data.get("color", "white")
    if color not in {"white", "black"}:
        color = "white"
    board = chess.Board()
    session["game_color"] = color
    session["game_moves"] = []
    session["game_active"] = True
    session["game_result"] = None
    session["game_opponent"] = "Stockfish" if ENGINE_PATH else "Bot"
    save_board(board)
    last_move = None
    message = "New game started."
    if color == "black":
        bot_move = choose_bot_move(board)
        if bot_move:
            san = push_move(board, bot_move)
            last_move = bot_move
            message = f"Bot played {san}."
    return jsonify(game_payload(board, message, last_move))


@app.route("/api/game/state")
@login_required
def api_game_state():
    board = get_board()
    if board is None:
        return jsonify({"success": True, "active": False})
    return jsonify(game_payload(board))


@app.route("/api/game/move", methods=["POST"])
@login_required
def api_game_move():
    board = get_board()
    if board is None:
        return jsonify({"success": False, "error": "Start a game first."}), 400
    if not session.get("game_active", False):
        return jsonify({"success": False, "error": "This game is already finished."}), 400
    if board.turn != player_turn():
        return jsonify({"success": False, "error": "Wait for the bot to move."}), 400
    move_text = (request.get_json() or {}).get("move", "").strip()
    if not move_text:
        return jsonify({"success": False, "error": "Type a move first."}), 400
    try:
        move = board.parse_san(move_text)
    except chess.InvalidMoveError:
        return jsonify({"success": False, "error": "That move is not valid notation."}), 400
    except chess.IllegalMoveError:
        return jsonify({"success": False, "error": "That move is illegal in this position."}), 400
    except chess.AmbiguousMoveError:
        return jsonify({"success": False, "error": "That move is ambiguous. Be more specific."}), 400
    push_move(board, move)
    if board.is_game_over():
        result, message = finish_game(board)
        payload = game_payload(board, message, move)
        payload["result"] = result
        return jsonify(payload)
    bot_move = choose_bot_move(board)
    if bot_move is None:
        result, message = finish_game(board)
        payload = game_payload(board, message)
        payload["result"] = result
        return jsonify(payload)
    bot_san = push_move(board, bot_move)
    if board.is_game_over():
        result, end_message = finish_game(board)
        payload = game_payload(board, f"Bot played {bot_san}. {end_message}", bot_move)
        payload["result"] = result
        return jsonify(payload)
    return jsonify(game_payload(board, f"Bot played {bot_san}.", bot_move))


@app.route("/api/game/resign", methods=["POST"])
@login_required
def api_game_resign():
    board = get_board()
    if board is None:
        return jsonify({"success": False, "error": "No game to resign from."}), 400
    player_color_name = session.get("game_color", "white")
    session["game_active"] = False
    session["game_result"] = "0-1" if player_color_name == "white" else "1-0"
    winner = "Black" if player_color_name == "white" else "White"
    return jsonify({
        "success": True,
        "result": session["game_result"],
        "message": f"{player_color_name.capitalize()} resigned. {winner} wins.",
    })


@app.route("/api/game/save", methods=["POST"])
@login_required
def api_game_save():
    board = get_board()
    moves = session.get("game_moves", [])
    if board is None or not moves:
        return jsonify({"success": False, "error": "There is no game to save."}), 400
    result = session.get("game_result") or result_for_board(board)
    if not result:
        return jsonify({"success": False, "error": "Finish the game or resign before saving."}), 400
    opponent = session.get("game_opponent", "Bot")
    replay_board = chess.Board()
    pgn_game = chess.pgn.Game()
    pgn_game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
    pgn_game.headers["Result"] = result
    if session.get("game_color", "white") == "white":
        pgn_game.headers["White"] = current_user.username
        pgn_game.headers["Black"] = opponent
    else:
        pgn_game.headers["White"] = opponent
        pgn_game.headers["Black"] = current_user.username
    node = pgn_game
    for san in moves:
        replay_move = replay_board.parse_san(san)
        node = node.add_variation(replay_move)
        replay_board.push(replay_move)
    game = Game(
        user_id=current_user.id,
        opponent=opponent,
        color=session.get("game_color", "white"),
        result=result,
        moves=len(moves),
        pgn=str(pgn_game),
    )
    db.session.add(game)
    db.session.commit()
    clear_game()
    return jsonify({"success": True, "game_id": game.id})


if __name__ == "__main__":
    app.run(debug=True)
