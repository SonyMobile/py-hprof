#!/usr/bin/env python3
#coding=utf8

from .heaprecord import HeapRecord

from ..offset import offset, AutoOffsets, idoffset
from ..types import JavaType

class PrimitiveArrayRecord(HeapRecord):
	TAG = 0x23

	_offsets = AutoOffsets(1,
			'ID',     idoffset(1),
			'STRACE', 4,
			'COUNT',  4,
			'TYPE',   1,
			'DATA')

	@property
	def id(self):
		return self._read_id(self._offsets.ID)

	@property
	def count(self):
		return self._read_uint(self._offsets.COUNT)

	@property
	def type(self):
		return self._read_jtype(self._offsets.TYPE)

	def __len__(self):
		return self._offsets.DATA.flatten(self.hf.idsize) + self.count * self.type.size()

	def __str__(self):
		return 'PrimitiveArrayRecord(type=%s, count=%d)' % (self.type, self.count)

	def __getitem__(self, ix):
		if 0 <= ix < self.count:
			t = self.type
			offset = self._offsets.DATA + ix * t.size()
			return self._read_jvalue(offset, t)
		else:
			raise IndexError('tried to read element %d in a size %d array' % (ix, self.count))
