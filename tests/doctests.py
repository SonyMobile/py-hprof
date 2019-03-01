import atexit
import doctest
import inspect

import hprof

hf = None

def setup(test):
	global hf
	if hf is None:
		hf = hprof.open('tests/java.hprof')
	test.globs['hf'] = hf
	dump, = hf.dumps()
	test.globs['dump'] = dump
	test.globs['car'], = (c for c in dump.find_instances('com.example.cars.Car') if c.make == 'Lolvo')
	test.globs['shortarray'] = test.globs['car'].wheelDimensions[0]
	test.globs['vehicles'] = next(dump.find_instances('com.example.cars.CarExample')).objs

@atexit.register
def cleanup():
	if hf is not None:
		hf.close()

def modules(m, seen):
	seen.add(m)
	yield m
	for name, subm in inspect.getmembers(m):
		if inspect.ismodule(subm) and subm.__name__.startswith('hprof') and subm not in seen:
			yield from modules(subm, seen)

def load_tests(loader, tests, ignore):
	for module in modules(hprof, set()):
		tests.addTests(doctest.DocTestSuite(module, setUp=setup))
	return tests
