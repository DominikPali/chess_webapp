# Data Storage

## Default Database Location
- SQLite database: `instance/notationlearner.db`

This is the default storage used when `DATABASE_URL` is not set.

## Persistent Models

### `User`
- Stores login identity and profile data.
- Fields:
  `id`, `username`, `email`, `password_hash`, `created_at`

### `Game`
- Stores one completed saved game for one user.
- Fields:
  `id`, `user_id`, `date_played`, `opponent`, `color`, `result`, `moves`, `pgn`, `fen_final`, `created_at`

### `Move`
- Stores move-by-move replay data for a saved game.
- Fields:
  `id`, `game_id`, `move_number`, `color`, `notation`, `fen_after`

### `ActiveGame`
- Stores live multiplayer room state.
- Fields:
  `id`, `code`, `white_user_id`, `black_user_id`, `fen`, `moves_json`, `fens_json`, `status`, `result`, `created_at`

## Session Storage
Solo games are stored in the Flask session while the game is active.

### Session Keys
- `game_fen`
  Current board FEN
- `game_moves`
  SAN moves played so far
- `game_fens`
  FEN snapshots after each move
- `game_opponent`
  Opponent label used for saving and UI
- `game_color`
  User-selected side
- `game_active`
  Boolean indicating whether the session game is still active

## PGN and FEN Usage
- SAN is used as the primary move input/output format.
- PGN is generated when a game is saved and stored on the `Game` row.
- FEN is used for:
  live board state,
  per-move replay snapshots,
  analysis navigation,
  multiplayer room synchronization.

## Transient vs Persistent State
- Transient:
  solo session state, current browser UI state, polling intervals in JS
- Persistent:
  users, completed games, per-move replay history, live multiplayer room state

## Preservation Notes
- The cleanup intentionally preserves existing SQLite data.
- Schema creation is now non-destructive.
- Local database files are runtime artifacts and should stay out of Git.
