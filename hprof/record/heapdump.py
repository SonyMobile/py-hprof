#!/usr/bin/env python3
#coding=utf8

from . import base

from .. import heaprecord
from ..errors import *

class HeapDumpSegment(base.Record):
	__slots__ = ()
	TAG = 28

	def __str__(self):
		return 'HeapDumpSegment(payloadsize=%s)' % (len(self) - base.offsets.BODY)

	def records(self):
		offset = base.offsets.BODY
		end = len(self)
		while offset < end:
			r = heaprecord.HeapRecord.create(self.hf, self.addr + offset)
			offset += len(r)
			if offset > end:
				raise FileFormatError('subrecord ends at 0x%x, dump segment ends at 0x%x' % (offset, end))
			yield r

class HeapDumpEnd(base.Record):
	__slots__ = ()
	TAG = 44

	def __init__(self, hf, addr):
		super().__init__(hf, addr)
		if len(self) != 9:
			raise FileFormatError('HeapDumpEnd payload at 0x%x is not empty: %s' % (self.addr, self))
