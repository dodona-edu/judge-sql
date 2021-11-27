#!/bin/bash

ROOT="$(dirname $(dirname $0))"

cd "$ROOT"

git submodule foreach git pull origin main
