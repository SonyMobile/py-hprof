#!/usr/bin/env python3
#coding=utf8

from struct import pack
from unittest import TestCase

import sys

def varying_idsize(cls):
	targetscope = sys.modules[cls.__module__]
	for sz in (2, 3, 4, 8):
		name = cls.__name__ + '_idsize%d' % sz
		if hasattr(targetscope, name):
			raise Exception('%s already exists' % name)
		sub = type(name, (cls,), {'idsize':sz})
		setattr(targetscope, name, sub)
	return None # don't even give them the original.

class HprofBuilder(object):
	def __init__(self, vstring, idsize, timestamp):
		self._idsize = idsize
		self._buf = bytearray()
		self._record_addrs = []
		self._writers = []
		with _Appender(self) as header:
			header.bytes(vstring)
			header.uint(idsize)
			header.uint(timestamp >> 32)
			header.uint(timestamp & 0xffffffff)

	def build(self):
		out = self._buf
		self._buf = None # no reuse!
		return tuple(self._record_addrs), out

	def record(self, tag, timestamp):
		self._record_addrs.append(len(self))
		return _Record(self, tag, timestamp)

	def _myturn(self, who):
		assert who not in self._writers
		self._writers.append(who)
		return len(self._buf)

	def _done(self, who):
		old = self._writers.pop()
		assert old is who
		return len(self._buf)

	def _append(self, who, b):
		assert who is self._writers[-1]
		if type(b) is int:
			self._buf.append(b)
		else:
			self._buf.extend(b)

	def __len__(self):
		return len(self._buf)


class _Appender(object):
	def __init__(self, hb):
		self._hb = hb

	def __enter__(self):
		self._start = self._hb._myturn(self)
		return self

	def __exit__(self, exctype, excval, tb):
		if exctype is not None:
			del self._hb._buf[self._start:] # rollback
		else:
			self._end = self._hb._done(self)

	def byte(self, b):
		self._hb._append(self, b)

	def bytes(self, b):
		if type(b) is str:
			b = b.encode('utf8')
		self._hb._append(self, b)

	def uint(self, u):
		self._hb._append(self, pack('>I', u))

	def ushort(self, u):
		self._hb._append(self, pack('>H', u))

	def id(self, ident):
		assert type(ident) is int
		assert ident >= 0
		# fold ident by xor, so it fits in idsize bytes.
		b = 0
		mask = (1 << (8 * self._hb._idsize)) - 1
		while ident > 0:
			b ^= ident & mask
			ident >>= (8 * self._hb._idsize)
		self._hb._append(self, b.to_bytes(self._hb._idsize, 'big'))
		return b

class _Record(_Appender):
	def __init__(self, hb, tag, timestamp):
		super().__init__(hb)
		self._tag = tag
		self._timestamp = timestamp

	def __enter__(self):
		out = super().__enter__()
		self.byte(self._tag)
		self.uint(self._timestamp)
		self.uint(0xfbadf00d) # will be replaced with a proper length in __exit__
		return out

	def __exit__(self, exctype, excval, tb):
		out = super().__exit__(exctype, excval, tb)
		if exctype is None:
			bodylen = self._end - self._start - 9
			self._hb._buf[self._start+5:self._start+9] = pack('>I', bodylen)
		return out

	def subrecord(self, tag):
		return _SubRecord(self._hb, tag)

class _SubRecord(_Appender):
	def __init__(self, hb, tag):
		super().__init__(hb)
		self._tag = tag

	def __enter__(self):
		out = super().__enter__()
		self.byte(self._tag)
		return out

