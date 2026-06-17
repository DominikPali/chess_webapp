"""Application factory package — builds and wires up the Flask app (config, DB, login, routes)."""

from pathlib import Path

from flask import Flask
from sqlalchemy import inspect, text

from .config import configure_app
from .extensions import db, login_manager
from .routes import register_routes


def _add_missing_columns():
    """One-shot schema shim for SQLite — keeps existing DBs working
    without an Alembic migration system."""
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()

    if "active_game" in table_names:
        cols = {c["name"] for c in inspector.get_columns("active_game")}
        if "activated_at" not in cols:
            with db.engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE active_game ADD COLUMN activated_at DATETIME")
                )

    if "user" in table_names:
        user_cols = {c["name"] for c in inspector.get_columns("user")}
        with db.engine.begin() as conn:
            for col in ("wins", "draws", "losses"):
                if col not in user_cols:
                    conn.execute(
                        text(
                            f"ALTER TABLE user ADD COLUMN {col} "
                            "INTEGER NOT NULL DEFAULT 0"
                        )
                    )


def create_app():
    """Build a configured Flask app: set paths, init extensions, register routes, and create/patch DB tables."""
    project_root = Path(__file__).resolve().parent.parent
    instance_path = project_root / "instance"
    app = Flask(
        __name__,
        instance_path=str(instance_path),
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
    )

    configure_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    register_routes(app)

    with app.app_context():
        db.create_all()
        _add_missing_columns()

    return app
