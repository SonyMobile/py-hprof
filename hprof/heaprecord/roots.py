#!/usr/bin/env python3
#coding=utf8

from .heaprecord import HeapRecord

from ..offset import offset, AutoOffsets, idoffset

class GcRoot(HeapRecord):
	__slots__ = ()

	@property
	def obj(self):
		objid = self._read_id(self.offsets.ID)
		return self.hf[objid]

	def __len__(self):
		return self.offsets.END.flatten(self.hf.idsize)

	def _info(self):
		return str(self.obj)

	def __str__(self):
		return '%s(%s)' % (type(self).__name__, self._info())

class UnknownRoot(GcRoot):
	__slots__ = ()
	TAG = 0xff
	offsets = AutoOffsets(1, 'ID', idoffset(1), 'END')


class ThreadRoot(GcRoot):
	__slots__ = ()
	TAG = 0x08
	offsets = AutoOffsets(1,
			'ID',     idoffset(1),
			'THREAD', 4,
			'STRACE', 4,
			'END')

	def _info(self):
		return super()._info() + ' from thread ???'
