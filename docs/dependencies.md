# Dependencies

## Backend Libraries

### Flask
- Main web framework.
- Used for routing, rendering templates, JSON responses, sessions, and application setup.

### Flask-Login
- Handles user session management.
- Used in auth routes and any route protected by `@login_required`.

### Flask-SQLAlchemy
- ORM and database integration.
- Used by the models and persistence code.

### python-chess
- Core chess engine library for rules and notation.
- Used to:
  parse SAN,
  validate legality,
  detect check/checkmate/draws,
  generate PGN,
  render SVG boards,
  analyze positions with Stockfish.

### PyMySQL
- Optional MySQL driver for explicit `DATABASE_URL` usage.

### Werkzeug
- Password hashing and checking.

### cryptography
- Supporting dependency commonly required by database/security-related packages in this environment.

## Frontend Libraries

### Bootstrap 5
- Layout, spacing, utility classes, and base UI styling.

### Bootstrap Icons
- Navigation and panel icons.

### Google Fonts
- `Playfair Display` for display typography.
- `Source Sans 3` for body text and controls.

## Runtime Dependencies Outside Python

### Stockfish
- Optional local binary used for hints and best-move analysis.
- The app remains functional without it.
