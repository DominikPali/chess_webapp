# Project Structure

## Top Level
- `app.py`
  Thin entrypoint that creates the Flask app and starts the development server.
- `app/`
  Core backend package. This is where the application logic now lives.
- `templates/`
  Jinja templates rendered by Flask.
- `static/`
  Frontend CSS, JavaScript, and image assets.
- `instance/`
  Local runtime data such as the SQLite database.
- `docs/`
  Documentation for architecture, storage, dependencies, and cleanup decisions.
- `requirements.txt`
  Python dependencies needed to run the project.
- `database_setup.py`
  Simple helper that initializes the configured database tables.

## Backend Package
- `app/__init__.py`
  App factory. Creates the Flask app, loads config, initializes extensions, registers routes, and ensures tables exist.
- `app/config.py`
  Runtime configuration for `SECRET_KEY`, `DATABASE_URL`, SQLite fallback, and `STOCKFISH_PATH`.
- `app/extensions.py`
  Shared Flask extensions: SQLAlchemy and Flask-Login.
- `app/models.py`
  ORM models for `User`, `Game`, `Move`, and `ActiveGame`.

## Route Modules
- `app/routes/pages.py`
  Server-rendered page routes for landing, about, play, and analysis pages.
- `app/routes/auth.py`
  Login, register, logout, profile, profile edit, and account deletion.
- `app/routes/game_api.py`
  Solo game APIs: new game, move submission, hint, state, resign, save.
- `app/routes/room_api.py`
  Multiplayer room APIs: create, join, state, move, resign, save.
- `app/routes/analysis_api.py`
  Analysis APIs: load saved game data, generate board SVG for a FEN, get best move.

## Service Modules
- `app/services/chess_helpers.py`
  Shared helpers for session game state, Stockfish access, board SVG rendering, and room code generation.
- `app/services/game_storage.py`
  Shared persistence logic for converting SAN move lists into PGN, final FEN, and saved database records.

## Frontend
- `templates/base.html`
  Shared shell for head assets, navbar, footer, and page blocks.
- `templates/index.html`
  Landing page.
- `templates/about.html`
  Project description page.
- `templates/login.html`
  Login and register page, controlled by the `mode` context variable.
- `templates/play.html`
  Game page for solo play and multiplayer rooms.
- `templates/profile.html`
  Profile and game history page.
- `templates/edit_profile.html`
  Profile editing form.
- `templates/analyse.html`
  Saved-game replay and analysis page.
- `static/style.css`
  Entire application styling.
- `static/main.js`
  Frontend behavior for play and analysis pages.
- `static/logo.png`
  Application logo.

## Runtime vs Source-Controlled Content
- Source code belongs in `app/`, `templates/`, `static/`, and `docs/`.
- Local runtime/generated files do not belong in Git:
  virtual environments, compiled Python caches, local database files, and operating-system metadata such as `.DS_Store`.
