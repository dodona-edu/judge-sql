#!/bin/bash

ROOT="$(dirname $(dirname $0))"

isort **/*.py
black **/*.py --line-length=120
