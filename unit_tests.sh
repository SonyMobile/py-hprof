#!/bin/bash

set -e

python3-coverage run --branch --include 'hprof/*' -m unittest discover test.unit
python3-coverage report -m --fail-under=100
