#!/usr/bin/env python3
# Copyright (C) 2019 Snild Dolkow
# Licensed under the LICENSE.

import unittest
from cProfile import Profile
from pstats import Stats

tests = unittest.defaultTestLoader.discover('test.accept')
runner = unittest.TextTestRunner()

prof = Profile()
prof.enable()
testresults = runner.run(tests)
prof.disable()

stats = Stats(prof)
stats.sort_stats('cumulative', 'tottime')
nprinted = 0
print()
print('PROFILE:')
import sys
import os.path

show_callers = 'callers' in sys.argv

def splitpath(p):
	out = []
	while True:
		p, component = os.path.split(p)
		if not component:
			out.reverse()
			return out
		out.append(component)

fmt = '%15s %7s %7s %7s %7s %s'
arg = ('ncalls', 'tottime', 'percall', 'cumtime', 'percall', 'function')
print(fmt % arg)
for func in stats.fcn_list:
	path, line, name = func
	ncalls, nrecursive, internal, total, callers = stats.stats[func]

	# skip some stuff we don't care about.
	if (
		path.endswith('/unittest/runner.py')
		or path.endswith('/unittest/suite.py')
		or '/test/accept/test_' in path
	):
		continue

	# shorten the path a bit.
	for syspath in sys.path:
		if syspath and path.startswith(syspath):
			path = splitpath(path)
			syspath = splitpath(syspath)
			path = path[len(syspath)-1:] # keep one parent
			path = os.path.join(*path)
			break

	if nrecursive == ncalls:
		callstr = '%d' % ncalls
	else:
		callstr = '%d/%d' % (nrecursive, ncalls)
	if path == '~' and line == 0:
		descr = name
	else:
		descr = '%-20s %s:%d' % (name, path, line)
	fmt = '%15s %7.3f %7.3f %7.3f %7.3f %s'
	arg = (callstr, internal, internal/nrecursive, total, total/ncalls, descr)
	print(fmt % arg)
	if show_callers:
		for caller, cstats in sorted(callers.items(), key=lambda p: -p[1][0]):
			path, line, name = caller
			ncalls, nrecursive, internal, total = cstats
			print('%51s %8d %7.3f %s' % ('->', ncalls, total, name))
	nprinted += 1
	if nprinted >= 20:
		break

if not testresults.wasSuccessful():
	sys.exit(1)
