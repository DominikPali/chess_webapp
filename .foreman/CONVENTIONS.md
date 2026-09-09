# Conventions — NotationLearner

Read this before starting any ticket.

## General
- Only edit files listed in the ticket's `owns`. Files under `reads` are context —
  read them, don't change them.
- Existing tests that aren't part of your ticket must keep passing.
- Run your ticket's exact `verify` commands yourself before considering it done.
- Don't worry about formatting — the Runner runs `ruff format` on your changed files
  automatically after every iteration, before the formatter-clean gate checks them. Focus
  on correctness, not style.
- One logical change per commit; don't reformat files you're not otherwise touching.

## About this project
Flask 3 web app for learning chess algebraic notation by typing moves instead of clicking
pieces — account management, solo play, multiplayer rooms (joined by a short code), saved
game history, replay/analysis with optional Stockfish hints. Tech: Flask, Flask-Login,
Flask-SQLAlchemy, python-chess, PyMySQL, Werkzeug.

- `app/`: application package (`__init__.py` = app factory, `config.py`, `extensions.py`,
  `models.py`).
- `app/routes/`: Flask blueprints — `pages.py` (page rendering), `auth.py` (login/register/
  profile), `game_api.py`, `room_api.py`, `analysis_api.py`.
- `app/services/`: `chess_helpers.py` (python-chess + Stockfish glue), `game_storage.py`
  (PGN read/write).
- `templates/`, `static/`: server-rendered Jinja2 + vanilla JS/CSS, no frontend build step.
- **No `tests/` directory exists yet** — this is a real, known gap, not something to paper
  over. A ticket whose `verify` command is a bare `pytest` with no test files will fail
  loudly (`no tests ran`, exit 5) — every ticket's own `verify` must target a test file the
  ticket itself creates.
- Local dev DB defaults to a SQLite file under Flask's `instance/` folder (`app/config.py`);
  no live database is needed to run static checks or a ticket's own unit tests.

## mypy — known baseline noise, not your fault
Running `mypy --explicit-package-bases .` today reports 11 pre-existing errors: `flask_login`
has no type stubs at all (no `types-flask-login` package exists to install — a permanent gap
in that library, not a project bug), and 4 `db.Model is not defined` errors from
Flask-SQLAlchemy's dynamically-generated declarative base (a well-known mypy limitation with
that ORM's classic API, not `flask-sqlalchemy-stubs` — that package targets a much older API
and doesn't help here). **Do not try to fix these as a side effect of an unrelated ticket.**
If a ticket's own `verify` list includes mypy, scope it to the specific file(s) the ticket
owns (e.g. `mypy --explicit-package-bases app/services/your_new_file.py`), not the whole
tree, so these known baseline errors don't fail your otherwise-correct work.

## Sandbox image
`.foreman/sandbox.Dockerfile` bakes in the exact pinned versions from `requirements.txt`
(the build context is `.foreman/` itself, so `requirements.txt` can't be `COPY`'d in — see
the Dockerfile's own comment). **If you add or bump a dependency, update both files.** mypy
and pytest are installed via plain `pip install` sharing the same environment as the
project's own dependencies, deliberately NOT `uv tool install` (a uv-tool-installed mypy
gets its own isolated venv and can't see flask/chess/sqlalchemy at all — confirmed live
during onboarding, phase 6). ruff stays `uv tool install`-ed; it doesn't need to resolve
imports.
