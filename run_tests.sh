#!/bin/bash
# Copyright (C) 2019 Snild Dolkow
# Copyright (C) 2020 Sony Mobile Communications Inc.
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
echo 'Running DOC tests...'
python3 -m unittest test.docs || fail 'DOC TEST FAILURES'

echo
echo
echo 'Running PYLINT...'
pylint3 -rn hprof || fail 'PYLINT FAILURES'
echo 'OK'

echo
echo
echo 'Running DOC GENERATION...'
./doc2html.py > hprof.html || fail 'DOC GENERATION FAILED'
echo 'OK'

echo
echo
echo 'Running ACCEPTANCE tests...'
python3 _run_acceptance.py "$@" || fail 'ACCEPTANCE TEST FAILURES'

tput setaf 2
echo
echo 'ALL TESTS OK'
echo
tput sgr0
