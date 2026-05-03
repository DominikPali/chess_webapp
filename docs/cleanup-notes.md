# Cleanup Notes

## What Was Removed Or Marked As Non-Essential

### Runtime Artifacts
- Virtual environment folders such as `.venv/`
- Root-level `bin/`, `include/`, and `lib/` runtime directories
- Compiled Python caches such as `__pycache__/`
- macOS metadata such as `.DS_Store`

These files are generated locally and are not part of the source code.

### Legacy Application Copy
- `notationlearner_app/`

This was an older copy of the project and duplicated source that is no longer needed by the live app.

### Dead Backend Structure
- Top-level `routes/`
- `app/game_logic/game.py`

These were not part of the current running Flask application and added confusion about the real execution path.

### Obsolete Template-Side Asset Copies
- `templates/logo.png`
- `templates/main.js`
- `templates/style.css`

The live app uses `static/` for assets, so these duplicates were unnecessary.

## What Was Intentionally Preserved
- Current page routes and API endpoints
- Current interface and workflows
- Current SQLite data in `instance/notationlearner.db`
- Current frontend assets in `static/`
- Current templates and overall visual layout

## Structural Simplifications Made
- Moved the large monolithic backend into focused modules under `app/`
- Centralized app setup, config, models, and route registration
- Centralized shared chess/session/persistence helpers
- Added a shared `templates/base.html` so common page chrome is defined once
- Replaced destructive schema-rebuild startup behavior with non-destructive table creation

## What Developers Should Recreate Locally Instead Of Committing
- Virtual environments
- Installed packages
- Local database files
- Python caches
- OS/editor metadata files
