#!/bin/bash
set -euo pipefail

ROOT="$(dirname "$(dirname "$0")")"

cd "$ROOT"

ruff check .
ruff format --check .
# --python is required: CI has no .venv and no activated venv, so without
# it ty resolves based on what's available, which varies by machine.
ty check --python "$(command -v python3)" sql_judge.py judge/
