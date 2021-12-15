#!/bin/bash

ROOT="$(dirname $(dirname $0))"

cd "$ROOT"

pytest \
    --pylama \
    --ignore="tests"\
    $@
