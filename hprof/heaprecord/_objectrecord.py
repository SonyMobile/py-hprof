#!/usr/bin/env python3
#coding=utf8

from ._heaprecord import Allocation

from .._errors import FieldNotFoundError
from .._offset import offset, AutoOffsets, idoffset
from .._types import JavaType


class Object(Allocation):
	HPROF_DUMP_TAG = 0x21

	_hprof_offsets = AutoOffsets(1,
		'ID',       idoffset(1),
		'STRACE',   4,
		'CLSID',    idoffset(1),
		'DATASIZE', 4,
		'DATA'
	)

	@property
	def hprof_class_id(self):
		return self._hprof_id(self._hproff.CLSID)

	def __len__(self):
		return self._hproff.DATA + self._hprof_uint(self._hproff.DATASIZE)

	def __str__(self):
		cname = super().hprof_class.hprof_name
		return 'Object(class=%s, id=0x%x)' % (cname, self.hprof_id)

	def __getattr__(self, name):
		return self[name]
