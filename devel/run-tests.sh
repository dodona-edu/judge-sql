#!/bin/bash

ROOT="$(dirname $(dirname $0))"

cd "$ROOT"

git submodule update --init

pytest -n auto \
    --cov \
    --cov-branch \
    --cov-report xml \
    --cov-report html \
    "tests/" $@
