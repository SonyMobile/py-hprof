from ._heaprecord import HeapRecord
from .._errors import *
from .._offset import AutoOffsets, idoffset

offsets = AutoOffsets(1,
	'TYPE', 4,
	'NAME', idoffset(1),
	'END')

class HeapDumpInfo(HeapRecord):
	'''Information about the current heap (Android ART-specific).

	Subsequent object records belong to the heap specified here.

	Members:
	hprof_file -- the HprofFile this record belongs to.
	hprof_addr -- the byte address of this record in hprof_file.
	'''

	HPROF_DUMP_TAG = 0xfe

	@property
	def type(self):
		'''the type of this heap -- an integer.'''
		return self._hprof_uint(offsets.TYPE)

	@property
	def name(self):
		'''the name of this heap.'''
		nameid = self._hprof_id(offsets.NAME)
		return self.hprof_file.name(nameid)

	@property
	def _hprof_len(self):
		return offsets.END.flatten(self.hprof_file.idsize)

	def __str__(self):
		return 'HeapDumpInfo(type=%d name=%s)' % (self.type, self.name)
