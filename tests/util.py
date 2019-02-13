#!/usr/bin/env python3
#coding=utf8

from struct import pack
from unittest import TestCase

def varying_idsize(targetscope):
    def idsize_decorator(cls):
        for sz in (2, 3, 4, 8):
            name = cls.__name__ + '_idsize%d' % sz
            sub = type(name, (cls,), {'idsize':sz})
            if sub in targetscope:
                raise Exception('%s already exists' % name)
            targetscope[name] = sub
        return None
    return idsize_decorator

class HprofBuilder(object):
	def __init__(self, vstring, idsize, timestamp):
		self._idsize = idsize
		self._buf = bytearray()
		self._record_addrs = []
		self._writer = None
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

	def __len__(self):
		return len(self._buf)


class _Appender(object):
	def __init__(self, hb):
		self._hb = hb

	def __enter__(self):
		if self._hb._writer is not None:
			raise Exception('write already in progress')
		self._hb._writer = self
		return self

	def __exit__(self, exctype, excval, tb):
		if self._hb._writer is not self:
			raise Exception('we lost control of the builder; data is probably corrupted')
		self._hb._writer = None

	def byte(self, b):
		self._hb._buf.append(b)

	def bytes(self, b):
		if type(b) is str:
			b = b.encode('utf8')
		self._hb._buf.extend(b)

	def uint(self, u):
		self._hb._buf.extend(pack('>I', u))

	def id(self, ident):
		assert type(ident) is int
		assert ident >= 0
		self._hb._buf.extend(ident.to_bytes(self._hb._idsize, 'big'))

class _Record(_Appender):
	def __init__(self, hb, tag, timestamp):
		super().__init__(hb)
		self._tag = tag
		self._timestamp = timestamp

	def __enter__(self):
		out = super().__enter__()
		self._start = len(self._hb._buf)
		self.byte(self._tag)
		self.uint(self._timestamp)
		self.uint(0xfbadf00d) # will be replaced with a proper length in __exit__
		return out

	def __exit__(self, exctype, excval, tb):
		if exctype is None:
			bodylen = len(self._hb._buf) - self._start - 9
			self._hb._buf[self._start+5:self._start+9] = pack('>I', bodylen)
		else:
			del self._hb._buf[self._start:]
		return super().__exit__(exctype, excval, tb)

