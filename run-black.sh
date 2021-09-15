#!/bin/sh

DIR="$(dirname $0)"

python -m black . --line-length=120
