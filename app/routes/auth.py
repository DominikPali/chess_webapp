"""Authentication and account routes — login, registration, logout, profile viewing/editing, and deletion."""

from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager
from app.models import Game, User
from app.services.chess_helpers import clear_session_game_state


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login callback that reloads the User object from the database given the id stored in the session."""
    return db.session.get(User, int(user_id))


def register_auth_routes(app):
    """Register all authentication and profile-management endpoints on the Flask app."""
    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Show the login form (GET) or verify credentials and start a session, redirecting to profile (POST)."""
        if current_user.is_authenticated:
            return redirect(url_for("profile"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for("profile"))
            flash("Invalid username or password.", "error")

        return render_template("login.html", mode="login")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        """Show the signup form (GET) or validate input and create a new hashed-password account (POST)."""
        if current_user.is_authenticated:
            return redirect(url_for("profile"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            if User.query.filter_by(username=username).first():
                flash("Username already taken.", "error")
            elif User.query.filter_by(email=email).first():
                flash("Email already registered.", "error")
            elif len(password) < 6:
                flash("Password must be at least 6 characters.", "error")
            else:
                db.session.add(
                    User(
                        username=username,
                        email=email,
                        password_hash=generate_password_hash(password),
                    )
                )
                db.session.commit()
                flash("Account created! Please log in.", "success")
                return redirect(url_for("login"))

        return render_template("login.html", mode="register")

    @app.route("/logout")
    @login_required
    def logout():
        """Clear any in-progress game state, end the user's login session, and return to the home page."""
        clear_session_game_state()
        logout_user()
        return redirect(url_for("index"))

    @app.route("/profile")
    @login_required
    def profile():
        """Render the current user's profile with their saved games listed newest-first."""
        games = (
            Game.query.filter_by(user_id=current_user.id)
            .order_by(Game.date_played.desc())
            .all()
        )
        return render_template("profile.html", games=games)

    @app.route("/profile/edit", methods=["GET", "POST"])
    @login_required
    def edit_profile():
        """Show the edit form (GET) or update username/email after checking they aren't taken by others (POST)."""
        if request.method == "POST":
            new_username = request.form.get("username", "").strip()
            new_email = request.form.get("email", "").strip()
            taken = User.query.filter_by(username=new_username).first()

            if taken and taken.id != current_user.id:
                flash("Username already taken.", "error")
            else:
                taken_email = User.query.filter_by(email=new_email).first()
                if taken_email and taken_email.id != current_user.id:
                    flash("Email already registered.", "error")
                else:
                    current_user.username = new_username
                    current_user.email = new_email
                    db.session.commit()
                    flash("Profile updated.", "success")
                    return redirect(url_for("profile"))

        return render_template("edit_profile.html")

    @app.route("/profile/delete", methods=["POST"])
    @login_required
    def delete_account():
        """Permanently delete the current user (cascading to their games), clear the session, and log out."""
        db.session.delete(current_user)
        db.session.commit()
        session.clear()
        logout_user()
        return redirect(url_for("index"))
