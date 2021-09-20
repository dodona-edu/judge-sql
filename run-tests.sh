#!/bin/sh

DIR="$(dirname $0)"

pytest -n auto --cov --cov-branch --cov-report html "tests/"
