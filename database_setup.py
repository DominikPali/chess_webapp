"""
Initialize the configured NotationLearner database tables.

Usage:
    python3 database_setup.py

The script respects the same configuration as the application:
- DATABASE_URL: optional explicit database connection string
- SECRET_KEY: ignored here but supported by the app
- STOCKFISH_PATH: ignored here but supported by the app

If DATABASE_URL is not set, the app uses the local SQLite database in `instance/`.
"""

from app import create_app
from app.extensions import db


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        print(f"Database ready: {app.config['SQLALCHEMY_DATABASE_URI']}")


if __name__ == "__main__":
    main()
