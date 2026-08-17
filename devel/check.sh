#!/bin/bash
set -euo pipefail

ROOT="$(dirname "$(dirname "$0")")"

cd "$ROOT"

# pylama's pytest plugin registers pytest_collect_file(path, parent), an arg pytest 8 removed, so
# `pytest --pylama` dies at startup with PluginValidationError. Run pylama directly instead: it
# decouples linting from the test runner and stops the lint job from collecting/running the suite.
pylama "$@"
