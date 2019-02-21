#!/usr/bin/env python3
#coding=utf8

from .heaprecord import Allocation

from ..offset import offset, AutoOffsets, idoffset
from ..types import JavaType

class Array(Allocation):
	@property
	def length(self):
		return self._read_uint(self._off.COUNT)

class PrimitiveArrayRecord(Array):
	TAG = 0x23

	_offsets = AutoOffsets(1,
			'ID',     idoffset(1),
			'STRACE', 4,
			'COUNT',  4,
			'TYPE',   1,
			'DATA')

	@property
	def type(self):
		return self._read_jtype(self._off.TYPE)

	def __len__(self):
		return self._off.DATA + self.length * self.type.size(self.hf.idsize)

	def __str__(self):
		return 'PrimitiveArrayRecord(type=%s, count=%d)' % (self.type, self.length)

	def __getitem__(self, ix):
		if 0 <= ix < self.length:
			t = self.type
			offset = self._off.DATA + ix * t.size(self.hf.idsize)
			return self._read_jvalue(offset, t)
		else:
			raise IndexError('tried to read element %d in a size %d array' % (ix, self.length))

class ObjectArrayRecord(Array):
	TAG = 0x22

	_offsets = AutoOffsets(1,
			'ID',	  idoffset(1),
			'STRACE', 4,
			'COUNT',  4,
			'CLSID',  idoffset(1),
			'DATA')

	def __len__(self):
		return self._off.DATA + self.length * self.hf.idsize

	def __str__(self):
		return 'ObjectArrayRecord(count=%d)' % self.length

	def __getitem__(self, ix):
		if 0 <= ix < self.length:
			return self._read_id(self._off.DATA + ix * self.hf.idsize)
		else:
			raise IndexError('tried to read element %d in a size %d array' % (ix, self.length))
