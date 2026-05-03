# Architecture

## High-Level Flow
- Flask serves HTML pages for the main interface.
- Templates render the page shell and mount page-specific sections.
- `static/main.js` calls JSON API endpoints for gameplay and analysis behavior.
- SQLAlchemy stores users, completed games, move history, and active multiplayer room state.
- `python-chess` validates moves, tracks board state, generates PGN, and renders SVG chessboards.
- Stockfish is used only when a hint or best-move request is made.

## App Initialization
- `app.py` imports `create_app()` from `app/__init__.py`.
- `create_app()` builds the Flask app, applies config, initializes SQLAlchemy and Flask-Login, registers routes, and calls `db.create_all()`.
- The default database is SQLite in `instance/notationlearner.db` unless `DATABASE_URL` is set.

## Page Rendering
- `/` renders the landing page.
- `/about` renders the project explanation page.
- `/play` renders the main play UI.
- `/play/<code>` renders the same play UI but injects `window.ROOM_CODE` so the frontend joins/polls a room.
- `/profile` shows account info and saved games.
- `/analyse/<game_id>` renders the replay page and injects `window.ANALYSE_GAME_ID`.

## Solo Game Flow
1. The play page calls `POST /api/game/new`.
2. The backend creates a fresh `python-chess` board and stores the active game in the Flask session.
3. The frontend sends SAN moves to `POST /api/game/move`.
4. The backend parses SAN with `python-chess`, validates legality, updates session state, and returns updated SVG, move list, and status flags.
5. If the user asks for a hint, `GET /api/game/hint` runs a Stockfish analysis for the current session board.
6. If the game ends or the user resigns, the frontend can call `POST /api/game/save`.
7. Saving converts the move list into PGN and stores a `Game` plus a set of `Move` rows.

## Multiplayer Flow
1. A user creates a room with `POST /api/room/create`.
2. The backend stores an `ActiveGame` record with a short code, current FEN, and move/FEN history as JSON text.
3. Another user joins through `POST /api/room/join`.
4. Both browsers poll `GET /api/room/state/<code>` to see moves and room status.
5. Moves are submitted to `POST /api/room/move/<code>`.
6. The backend enforces turn order based on the room FEN and player assignment.
7. When finished, either user can save the game into their own history through `POST /api/room/save/<code>`.

## Analysis Flow
1. The analysis page loads saved game data from `GET /api/analyse/<game_id>`.
2. The backend returns PGN, metadata, move list, and the starting board SVG.
3. The frontend navigates through positions by sending FENs to `POST /api/analyse/svg`.
4. Optional best-move analysis uses `POST /api/analyse/bestmove`.

## Why Data Is Split This Way
- Active solo games live in the session because they are temporary and single-user.
- Active multiplayer games live in the database because two users need shared state.
- Completed games live in normalized tables so the profile and replay pages can query them efficiently.
