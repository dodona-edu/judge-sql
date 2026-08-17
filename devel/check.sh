#!/bin/bash
set -euo pipefail

ROOT="$(dirname "$(dirname "$0")")"

cd "$ROOT"

ruff check .
ruff format --check .
mypy sql_judge.py judge/
