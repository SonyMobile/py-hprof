from . import _base

from .. import heap
from .._errors import *

class HeapDumpSegment(_base.Record):
	TAG = 28

	def __str__(self):
		return 'HeapDumpSegment(payloadsize=%s)' % (self._hprof_len - _base.offsets.BODY)

	def records(self):
		offset = _base.offsets.BODY
		end = self._hprof_len
		while offset < end:
			r = heap.create(self.hprof_file, self.hprof_addr + offset)
			offset += r._hprof_len
			if offset > end:
				raise FileFormatError('subrecord ends at 0x%x, dump segment ends at 0x%x' % (offset, end))
			yield r

class HeapDumpEnd(_base.Record):
	TAG = 44
