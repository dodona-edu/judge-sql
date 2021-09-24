#!/bin/sh

ROOT="$(dirname $(dirname $0))"

cd "$ROOT"
pytest -n auto --cov --cov-branch --cov-report html "tests/" $@
