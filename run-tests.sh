#!/bin/sh

DIR="$(dirname $0)"

python -m unittest discover $DIR "*_test.py" $@
