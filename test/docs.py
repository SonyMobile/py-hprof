# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

import atexit
import doctest
import inspect

import hprof

hf = None

def setup(test):
	global hf
	if hf is None:
		hf = hprof.open('testdata/example-java.hprof.bz2')
	test.globs['hf'] = hf
	test.globs['heap'], = hf.heaps

@atexit.register
def cleanup():
	global hf
	if hf is not None:
		hf.close()
		hf = None

def modules(m, seen):
	seen.add(m)
	yield m
	for name, subm in inspect.getmembers(m):
		if inspect.ismodule(subm) and subm.__name__.startswith('hprof') and subm not in seen:
			yield from modules(subm, seen)

def load_tests(loader, tests, ignore):
	for module in modules(hprof, set()):
		tests.addTests(doctest.DocTestSuite(
			module,
			setUp=setup,
			optionflags=doctest.ELLIPSIS
		))
	tests.addTests(doctest.DocFileSuite(
		'../README.md',
		setUp=setup,
		optionflags=doctest.ELLIPSIS
	))
	return tests
