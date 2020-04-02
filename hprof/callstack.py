# Copyright (C) 2019 Snild Dolkow
# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

'''
hprof files can contain callstacks. This module will be used to model them.
However, it is not done yet.
'''

class Frame(object):
	''' A callstack frame. '''
	__slots__ = ('method', 'signature', 'sourcefile', 'class_name', 'line')

class Trace(list):
	''' A callstack. '''
	__slots__ = ('thread', 'frames')
