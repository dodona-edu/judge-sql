#!/bin/bash
set -euo pipefail

ROOT="$(dirname "$(dirname "$0")")"

cd "$ROOT"

git submodule foreach git fetch origin main
git submodule foreach git checkout main
