#!/usr/bin/env python3
# Copyright (C) 2019 Snild Dolkow
# Licensed under the LICENSE.

import hprof
import sys

for path in sys.argv[1:]:
	def progress(txt, part, total):
		if total:
			print('%s: %s %d%%' % (path, txt, 100*part//total), end='')
		elif part is not None:
			print('%s: %s %d...' % (path, txt, part), end='')
		else:
			print('%s: %s...' % (path, txt), end='')
		print(20*' ', '\r', end='')
	with hprof.open(path, progress) as hf:
		print(path, 40*' ')
		if not hf.unhandled:
			print('    <no unhandled records>')
		for rtype in sorted(hf.unhandled):
			print('    %4d: %d' % (rtype, hf.unhandled[rtype]))
