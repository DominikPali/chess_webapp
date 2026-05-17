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
    if "active_game" not in inspector.get_table_names():
        return
    cols = {c["name"] for c in inspector.get_columns("active_game")}
    if "activated_at" not in cols:
        with db.engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE active_game ADD COLUMN activated_at DATETIME")
            )


def create_app():
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
