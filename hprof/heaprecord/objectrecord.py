#!/usr/bin/env python3
#coding=utf8

from .heaprecord import HeapRecord

from ..offset import offset, AutoOffsets, idoffset

offsets = AutoOffsets(1,
	'ID',       idoffset(1),
	'STRACE',   4,
	'CLSID',    idoffset(1),
	'DATASIZE', 4,
	'DATA'
)


class ObjectRecord(HeapRecord):
	__slots__ = ()
	TAG = 0x21

	@property
	def id(self):
		return self._read_id(offsets.ID)

	@property
	def datalen(self):
		return self._read_uint(offsets.DATASIZE)

	def __len__(self):
		return offsets.DATA.flatten(self.hf.idsize) + self.datalen

	def __str__(self):
		return 'ObjectRecord(id=0x%x)' % self.id
