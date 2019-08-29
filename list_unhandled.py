#!/usr/bin/env python3

import hprof
import sys

for path in sys.argv[1:]:
	hf = hprof.open(path)
	print(path)
	for rtype in sorted(hf.unhandled):
		print('    %4d: %d' % (rtype, hf.unhandled[rtype]))
