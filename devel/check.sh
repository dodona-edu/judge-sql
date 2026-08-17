#!/bin/bash
set -euo pipefail

ROOT="$(dirname "$(dirname "$0")")"

cd "$ROOT"

ruff check .
ruff format --check .
# --python is required: without it, ty falls back to whatever python3 happens to be first on
# PATH, which on a dev machine with several interpreters installed (pyenv/mise/asdf, ...) is not
# reliably the one requirements-dev.txt was installed into, and ty then silently type-checks
# against the wrong site-packages. Resolving it explicitly here keeps local runs and CI identical.
ty check --python "$(command -v python3)" sql_judge.py judge/
