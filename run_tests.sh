#!/bin/bash
# Copyright (C) 2019 Snild Dolkow
# Licensed under the LICENSE.

function fail() {
	tput setaf 1
	echo "$@"
	tput sgr0
	exit 1
}

echo 'Running UNIT tests...'
python3-coverage run --branch --include 'hprof/*' -m unittest discover test.unit || fail 'UNIT TEST FAILURES'

echo
echo
echo 'COVERAGE:'
python3-coverage report -m --fail-under=100 || fail 'INCOMPLETE COVERAGE'

echo
echo
echo 'Running ACCEPTANCE tests...'
python3 _run_acceptance.py "$@" || fail 'ACCEPTANCE TEST FAILURES'

tput setaf 2
echo
echo 'ALL TESTS OK'
echo
tput sgr0
