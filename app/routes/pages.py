"""Page routes — serve the rendered HTML pages (home, about, play, multiplayer room, and game analysis)."""

from flask import render_template
from flask_login import current_user, login_required

from app.models import ActiveGame, Game
from app.services.chess_helpers import cleanup_expired_rooms


def register_page_routes(app):
    """Register the static HTML page endpoints on the Flask app."""
    @app.route("/")
    def index():
        """Render the public landing/home page."""
        return render_template("index.html")

    @app.route("/about")
    def about():
        """Render the static About page describing the project."""
        return render_template("about.html")

    @app.route("/play")
    @login_required
    def play():
        """Render the play page where a logged-in user sets up and plays a game."""
        return render_template("play.html")

    @app.route("/play/<code>")
    @login_required
    def play_room(code):
        """Render the play page for a specific multiplayer room, 404-ing if the room code doesn't exist."""
        cleanup_expired_rooms()
        ActiveGame.query.filter_by(code=code.upper()).first_or_404()
        return render_template("play.html", room_code=code.upper())

    @app.route("/analyse/<int:game_id>")
    @login_required
    def analyse(game_id):
        """Render the analysis page for one of the current user's saved games (404 if not theirs)."""
        game = Game.query.filter_by(id=game_id, user_id=current_user.id).first_or_404()
        return render_template("analyse.html", game=game)
