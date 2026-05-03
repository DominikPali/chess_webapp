from pathlib import Path

from flask import Flask

from .config import configure_app
from .extensions import db, login_manager
from .routes import register_routes


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

    return app
