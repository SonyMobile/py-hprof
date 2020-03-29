# Copyright (C) 2019 Snild Dolkow
# Licensed under the LICENSE.

class Frame(object):
	__slots__ = ('method', 'signature', 'sourcefile', 'class_name', 'line')

class Trace(list):
	__slots__ = ('thread', 'frames')
