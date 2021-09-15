#!/bin/sh

DIR="$(dirname $0)"

pylint `ls -R|grep .py$|xargs`
