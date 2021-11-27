#!/bin/bash

ROOT="$(dirname $(dirname $0))"

cd "$ROOT"

git submodule update --remote
