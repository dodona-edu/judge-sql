#!/bin/bash

ROOT="$(dirname $(dirname $0))"

flakehell lint **/*.py
