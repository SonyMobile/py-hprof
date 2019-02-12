#!/usr/bin/env python3
#coding=utf8

from mmap import mmap, MAP_PRIVATE, PROT_READ
import struct

from .errors import *

def untuple(t):
	assert len(t) == 1
	return t[0]

class BinaryFile(object):
	def __init__(self, path):
		self._f = open(path, 'rb')
		self._data = mmap(self._f.fileno(), 0, MAP_PRIVATE, PROT_READ);

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

	def close(self):
		self._data.close()
		self._data = None
		self._f.close()
		self._f = None

	def stream(self, start_addr=0):
		return BinaryStream(self._data, start_addr)

	def __getattr__(self, name):
		''' return a wrapper for a single read through a Stream, if such a function exists. '''
		def stream_wrapper(addr, *args, **kwargs):
			s = self.stream(addr)
			f = getattr(s, name)
			return f(*args, **kwargs)
		return stream_wrapper

class BinaryStream(object):
	def __init__(self, data, startaddr):
		self._data = data
		self._addr = startaddr

	def skip(self, nbytes):
		self.jump_to(self._addr + nbytes)

	def jump_to(self, addr):
		if addr < 0 or addr > len(self._data):
			raise EofError(addr, len(self._data))
		self._addr = addr

	def _consume_bytes(self, nbytes, conversion):
		start = self._addr
		length = len(self._data)
		if start < 0 or start > length:
			raise EofError(start, length)
		if nbytes is not None:
			if nbytes < 0:
				raise ValueError('invalid nbytes', nbytes)
			end = start + nbytes
			if end > length:
				raise EofError(end, length)
			next = end
		else:
			end = start
			while end < length:
				if self._data[end] == 0:
					break
				end += 1
			else:
				raise EofError(end, length)
			next = end + 1 # consume the zero byte as well
		out = conversion(self._data[start:end])
		self._addr = next # conversion succeeded; consume the bytes.
		return out

	def read_ascii(self, nbytes=None):
		''' Read an ascii string of nbytes. If nbytes is None, read until a zero byte is found. '''
		return self._consume_bytes(nbytes, lambda b: b.decode('ascii'))

	def read_utf8(self, nbytes):
		''' Read an utf8 string of nbytes. Note: byte count, not character count! '''
		return self._consume_bytes(nbytes, lambda b: b.decode('utf8'))

	def _read_value(self, fmt):
		fmt = '>' + fmt
		n = struct.calcsize(fmt)
		return self._consume_bytes(n, lambda b: untuple(struct.unpack(fmt, b)))

	def read_byte(self):
		return self._read_value('B')

	def read_uint(self):
		return self._read_value('I')

	def read_int(self):
		return self._read_value('i')
