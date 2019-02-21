#!/usr/bin/env python3
#coding=utf8

from .heaprecord import Allocation

from ..offset import offset, AutoOffsets, idoffset
from ..types import JavaType

class Array(Allocation):
	@property
	def length(self):
		return self._hprof_uint(self._hproff.COUNT)

class PrimitiveArrayRecord(Array):
	HPROF_DUMP_TAG = 0x23

	_hprof_offsets = AutoOffsets(1,
			'ID',     idoffset(1),
			'STRACE', 4,
			'COUNT',  4,
			'TYPE',   1,
			'DATA')

	@property
	def hprof_elem_type(self):
		return self._hprof_jtype(self._hproff.TYPE)

	def __len__(self):
		return self._hproff.DATA + self.length * self.hprof_elem_type.size(self.hprof_file.idsize)

	def __str__(self):
		return 'PrimitiveArrayRecord(type=%s, count=%d)' % (self.hprof_elem_type, self.length)

	def __getitem__(self, ix):
		if 0 <= ix < self.length:
			t = self.hprof_elem_type
			offset = self._hproff.DATA + ix * t.size(self.hprof_file.idsize)
			return self._hprof_jvalue(offset, t)
		else:
			raise IndexError('tried to read element %d in a size %d array' % (ix, self.length))

class ObjectArrayRecord(Array):
	HPROF_DUMP_TAG = 0x22

	_hprof_offsets = AutoOffsets(1,
			'ID',	  idoffset(1),
			'STRACE', 4,
			'COUNT',  4,
			'CLSID',  idoffset(1),
			'DATA')

	def __len__(self):
		return self._hproff.DATA + self.length * self.hprof_file.idsize

	def __str__(self):
		return 'ObjectArrayRecord(count=%d)' % self.length

	def __getitem__(self, ix):
		if 0 <= ix < self.length:
			return self._hprof_id(self._hproff.DATA + ix * self.hprof_file.idsize)
		else:
			raise IndexError('tried to read element %d in a size %d array' % (ix, self.length))
