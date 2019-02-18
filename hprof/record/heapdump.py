#!/usr/bin/env python3
#coding=utf8

from . import base

from .. import heaprecord
from ..errors import *

class HeapDumpSegment(base.Record):
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
	TAG = 44
