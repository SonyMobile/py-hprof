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
		return self._read_id(self._off.ID)

	@property
	def count(self):
		return self._read_uint(self._off.COUNT)

	@property
	def type(self):
		return self._read_jtype(self._off.TYPE)

	def __len__(self):
		return self._off.DATA + self.count * self.type.size(self.hf.idsize)

	def __str__(self):
		return 'PrimitiveArrayRecord(type=%s, count=%d)' % (self.type, self.count)

	def __getitem__(self, ix):
		if 0 <= ix < self.count:
			t = self.type
			offset = self._off.DATA + ix * t.size(self.hf.idsize)
			return self._read_jvalue(offset, t)
		else:
			raise IndexError('tried to read element %d in a size %d array' % (ix, self.count))

class ObjectArrayRecord(HeapRecord):
	TAG = 0x22

	_offsets = AutoOffsets(1,
			'ID',	  idoffset(1),
			'STRACE', 4,
			'COUNT',  4,
			'CLSID',  idoffset(1),
			'DATA')

	@property
	def id(self):
		return self._read_id(self._off.ID)

	@property
	def count(self):
		return self._read_uint(self._off.COUNT)

	def __len__(self):
		return self._off.DATA + self.count * self.hf.idsize

	def __str__(self):
		return 'ObjectArrayRecord(count=%d)' % self.count

	def __getitem__(self, ix):
		if 0 <= ix < self.count:
			return self._read_id(self._off.DATA + ix * self.hf.idsize)
		else:
			raise IndexError('tried to read element %d in a size %d array' % (ix, self.count))
