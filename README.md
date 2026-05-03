# NotationLearner

NotationLearner is a Flask web app for learning chess algebraic notation by playing full games through typed moves instead of clicking pieces. The current interface includes account management, solo play, multiplayer rooms, game saving, and replay/analysis with optional Stockfish hints.

## Features
- User registration, login, profile editing, and account deletion
- Solo notation-based chess games stored in the browser session
- Multiplayer rooms joined with a short code
- Saved game history per user
- Replay/analysis view with move navigation
- Optional Stockfish hints during play and analysis

## Tech Stack
- Python 3
- Flask
- Flask-Login
- Flask-SQLAlchemy
- python-chess
- PyMySQL
- Werkzeug
- Bootstrap 5

## Project Layout
- `app.py`: thin runtime entrypoint
- `app/`: application package
- `templates/`: server-rendered HTML templates
- `static/`: frontend JavaScript, CSS, and images
- `instance/`: local runtime database files
- `docs/`: project documentation
- `requirements.txt`: Python dependencies

More detail is in [docs/project-structure.md](/Users/dominik/Desktop/coding/CSIO_chess_webapp/docs/project-structure.md).

## Setup
1. Create a virtual environment:
```bash
python3 -m venv .venv
```
2. Activate it:
```bash
source .venv/bin/activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Initialize the database:
```bash
python3 database_setup.py
```
5. Run the app:
```bash
python3 app.py
```

The app runs on `http://127.0.0.1:5001`.

## Configuration
- `DATABASE_URL`: optional explicit database URL. If omitted, the app uses SQLite at `instance/notationlearner.db`.
- `SECRET_KEY`: Flask secret key for session signing.
- `STOCKFISH_PATH`: optional path to the Stockfish binary. If omitted, the app tries common local install paths.

## Database Behavior
- Default local development storage is SQLite in `instance/notationlearner.db`.
- The current schema is created non-destructively with `db.create_all()`.
- Existing SQLite data is preserved.
- If you want to use MySQL or another SQLAlchemy-supported database, set `DATABASE_URL` explicitly.

## Stockfish
Hints and best-move analysis are optional. If Stockfish is not installed or the binary cannot be found, the app still works and returns a graceful error for hint requests.

## Documentation
- [docs/project-structure.md](/Users/dominik/Desktop/coding/CSIO_chess_webapp/docs/project-structure.md)
- [docs/architecture.md](/Users/dominik/Desktop/coding/CSIO_chess_webapp/docs/architecture.md)
- [docs/data-storage.md](/Users/dominik/Desktop/coding/CSIO_chess_webapp/docs/data-storage.md)
- [docs/dependencies.md](/Users/dominik/Desktop/coding/CSIO_chess_webapp/docs/dependencies.md)
- [docs/cleanup-notes.md](/Users/dominik/Desktop/coding/CSIO_chess_webapp/docs/cleanup-notes.md)
