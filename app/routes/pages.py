from flask import render_template
from flask_login import current_user, login_required

from app.models import ActiveGame, Game
from app.services.chess_helpers import cleanup_expired_rooms


def register_page_routes(app):
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/play")
    @login_required
    def play():
        return render_template("play.html")

    @app.route("/play/<code>")
    @login_required
    def play_room(code):
        cleanup_expired_rooms()
        ActiveGame.query.filter_by(code=code.upper()).first_or_404()
        return render_template("play.html", room_code=code.upper())

    @app.route("/analyse/<int:game_id>")
    @login_required
    def analyse(game_id):
        game = Game.query.filter_by(id=game_id, user_id=current_user.id).first_or_404()
        return render_template("analyse.html", game=game)
