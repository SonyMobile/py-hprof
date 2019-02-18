#!/usr/bin/env python3
#coding=utf8

from .heaprecord import HeapRecord
from ..errors import *
from ..offset import AutoOffsets, idoffset

offsets = AutoOffsets(1,
	'TYPE', 4,
	'NAME', idoffset(1),
	'END')

class HeapDumpInfo(HeapRecord):
	TAG = 0xfe

	@property
	def type(self):
		return self._read_uint(offsets.TYPE)

	@property
	def name(self):
		nameid = self._read_id(offsets.NAME)
		return self.hf.name(nameid)

	def __len__(self):
		return offsets.END.flatten(self.hf.idsize)

	def __str__(self):
		return 'HeapDumpInfo(type=%d name=%s)' % (self.type, self.name)
