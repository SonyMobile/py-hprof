# Copyright (C) 2019 Sony Mobile Communications Inc.
# Licensed under the LICENSE

from . import _base

from .. import heap
from .._errors import *

class HeapDumpSegment(_base.Record):
	'''One segment of a segmented heap dump. Contains heap object records and metadata.

	Members:
	hprof_file -- the HprofFile this record belongs to.
	hprof_addr -- the byte address of this record in hprof_file.
	'''

	TAG = 28

	def __str__(self):
		return 'HeapDumpSegment(payloadsize=%s)' % (self._hprof_len - _base.offsets.BODY)

	def records(self):
		'''yield all the internal records of this segment.'''
		offset = _base.offsets.BODY
		end = self._hprof_len
		while offset < end:
			r = heap.create(self.hprof_file, self.hprof_addr + offset)
			offset += r._hprof_len
			if offset > end:
				raise FileFormatError('subrecord ends at 0x%x, dump segment ends at 0x%x' % (offset, end))
			yield r

class HeapDumpEnd(_base.Record):
	'''Marks the end of a segmented heap dump.

	Members:
	hprof_file -- the HprofFile this record belongs to.
	hprof_addr -- the byte address of this record in hprof_file.
	'''

	TAG = 44
