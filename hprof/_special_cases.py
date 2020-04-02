# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

'''
This module contains code for handling some Java classes in specific ways, e.g.
making str() return the actual text of a java.lang.String.
'''

import codecs

def _jstr_to_str(self):
	''' get the string contents of a java.lang.String '''

	data = getattr(self, 'value', None)
	if data is not None:
		# OpenJDK has a 'coder' attribute that tells us the encoding:
		# https://github.com/openjdk/jdk/blob/6c9d6507/src/java.base/share/classes/java/lang/String.java#L163
		coder = getattr(self, 'coder', None)

		if len(data) == 0:
			return ''
		elif isinstance(data[0], bytes) or isinstance(data[0], int):
			# Could be ART/Android 'compressed' ascii bytes, or OpenJDK bytes

			static_latin1 = getattr(self, 'LATIN1', None)
			static_utf16  = getattr(self, 'UTF16',  None)

			if coder is None:
				# could be Android/ART 'compressed'
				bytes_encoding = 'ascii'
			elif coder == static_latin1:
				bytes_encoding = 'latin-1'
			elif coder == static_utf16:
				# big- or little-endian? May depend on the machine the hprof came from.
				# Let's guess little-endian.
				bytes_encoding = 'utf-16-le'
			else:
				raise ValueError('unknown string class encoding')
			return bytes(b&0xff for b in data).decode(bytes_encoding)
		elif coder is None and isinstance(data[0], str):
			# Looks like ART/Android 'uncompressed' utf16 chars.
			# char arrays may have surrogate pairs that should be merged into
			# real unicode characters. The simplest solution is to flatten them
			# to bytes, then decode them properly.
			joined = ''.join(data)
			flattened = codecs.encode(joined, 'utf-16-be', 'surrogatepass')
			return flattened.decode('utf-16-be')

	# alright, let the wrapper handle it.
	raise TypeError('unknown string class layout')


def _wrap_with_fallback(old, new):
	def fallback_wrapper(*args, **kwargs):
		''' calls the replacement function; if it fails, calls the original. '''
		try:
			return new(*args, **kwargs)
		except Exception: # pylint: disable=broad-except
			if old is None:
				raise
			return old(*args, **kwargs)
	return fallback_wrapper

def add(hprof_file, clsname, method_name, func):
	''' add a special function onto a class. '''
	for heap in hprof_file.heaps:
		for cls in heap.classes.get(clsname, ()):
			old = getattr(cls, method_name, None)
			wrapper = _wrap_with_fallback(old, func)
			setattr(cls, method_name, wrapper)

def setup_builtins(hf):
	''' setup all special case builtins. '''
	add(hf, 'java.lang.String', '__str__', _jstr_to_str)
