#!/bin/sh

ROOT="$(dirname $(dirname $0))"

pip3 install -r "$ROOT/requirements-dev.txt"
