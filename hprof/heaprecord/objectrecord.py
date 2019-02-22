#!/usr/bin/env python3
#coding=utf8

from .heaprecord import Allocation

from ..errors import FieldNotFoundError
from ..offset import offset, AutoOffsets, idoffset
from ..types import JavaType


class ObjectRecord(Allocation):
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
		return 'ObjectRecord(id=0x%x)' % self.hprof_id

	def __getattr__(self, name):
		return self[name]
