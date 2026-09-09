FROM python:3.12-slim

# mypy and pytest installed via plain `pip install` into the SAME global environment as the
# project's own dependencies below, deliberately NOT `uv tool install` — a uv-tool-installed
# mypy gets its own isolated venv and cannot see any other package on the system, so it
# reports "Cannot find implementation or library stub" for flask/chess/sqlalchemy/etc. even
# though they're genuinely installed one RUN layer down (confirmed live: `uv tool install
# mypy` + a separate `pip install flask ...` fails this way; sharing one environment via pip
# for both does not). ruff has no such issue (it's a static linter, not an import resolver),
# so it stays uv-tool-installed for the same isolation benefits everywhere else in this repo.
RUN pip install --no-cache-dir uv && uv tool install ruff
ENV PATH="/root/.local/bin:${PATH}"

# Baked in rather than `pip install -r requirements.txt` at verify time: the build CONTEXT
# is .foreman/ (build_sandbox_image() passes dockerfile.parent, not the project root), so
# requirements.txt isn't reachable to COPY here. Pinned to match requirements.txt exactly —
# keep these in sync by hand when that file changes (checked by CONVENTIONS.md's own note).
RUN pip install --no-cache-dir \
    flask==3.0.0 \
    flask-sqlalchemy==3.1.1 \
    flask-login==0.6.3 \
    python-chess==1.999 \
    pymysql==1.1.0 \
    werkzeug==3.0.1 \
    cryptography==41.0.7 \
    types-PyMySQL \
    mypy \
    pytest

WORKDIR /workspace
