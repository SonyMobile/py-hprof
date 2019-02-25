#!/usr/bin/env python3
#coding=utf8

from ._heaprecord import Allocation

from .._errors import FieldNotFoundError
from .._offset import offset, AutoOffsets, idoffset
from .._types import JavaType

class Array(Allocation):
	@property
	def length(self):
		return self._hprof_uint(self._hproff.COUNT)

class PrimitiveArray(Array):
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

	@property
	def hprof_class_id(self):
		return self.hprof_file.get_primitive_array_class_info(self.hprof_elem_type).class_id

	@property
	def _hprof_len(self):
		return self._hproff.DATA + self.length * self.hprof_elem_type.size(self.hprof_file.idsize)

	def __str__(self):
		return 'PrimitiveArray(type=%s, id=0x%x, count=%d)' % (self.hprof_elem_type, self.hprof_id, self.length)

	def __getitem__(self, ix):
		if type(ix) is int:
			if 0 <= ix < self.length:
				t = self.hprof_elem_type
				offset = self._hproff.DATA + ix * t.size(self.hprof_file.idsize)
				return self._hprof_jvalue(offset, t)
			else:
				raise IndexError('tried to read element %d in a size %d array' % (ix, self.length))
		else:
			# it's a field access; fall back to normal object field handling
			return super().__getitem__(ix)

class ObjectArray(Array):
	HPROF_DUMP_TAG = 0x22

	_hprof_offsets = AutoOffsets(1,
			'ID',	  idoffset(1),
			'STRACE', 4,
			'COUNT',  4,
			'CLSID',  idoffset(1),
			'DATA')

	@property
	def _hprof_len(self):
		return self._hproff.DATA + self.length * self.hprof_file.idsize

	def __str__(self):
		return 'ObjectArray(id=0x%x, count=%d)' % (self.hprof_id, self.length)

	@property
	def hprof_class_id(self):
		return self._hprof_id(self._hproff.CLSID)

	def __getitem__(self, ix):
		if type(ix) is int:
			# it's an array read!
			if 0 <= ix < self.length:
				v = self._hprof_id(self._hproff.DATA + ix * self.hprof_file.idsize)
				return self.hprof_heap.dump.get_object(v)
			else:
				raise IndexError('tried to read element %d in a size %d array' % (ix, self.length))
		else:
			# it's a field access; fall back to normal object field handling
			return super().__getitem__(ix)
