"""Application configuration — sets secret key, database URI, and locates the Stockfish engine binary."""

import os


def _resolve_stockfish_path(configured_path):
    """Return the first Stockfish binary that exists from the configured path plus common install locations."""
    default_path = configured_path or "/usr/local/bin/stockfish"
    candidate_paths = [
        default_path,
        "/opt/homebrew/bin/stockfish",
        "/usr/bin/stockfish",
        os.path.expanduser("~/stockfish/stockfish"),
    ]

    for path in candidate_paths:
        if path and os.path.exists(path):
            return path

    return default_path


def configure_app(app):
    """Populate app.config from environment variables, falling back to sensible local development defaults."""
    os.makedirs(app.instance_path, exist_ok=True)

    sqlite_path = os.path.join(app.instance_path, "notationlearner.db")
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY",
        "dev-secret-key-change-in-prod",
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{sqlite_path}",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["STOCKFISH_PATH"] = _resolve_stockfish_path(
        os.environ.get("STOCKFISH_PATH")
    )
