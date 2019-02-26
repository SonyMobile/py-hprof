from . import _base
from .._offset import *

class ClassLoad(_base.Record):
	'''Information about a class being loaded.

	Members:
	hprof_file -- the HprofFile this record belongs to.
	hprof_addr -- the byte address of this record in hprof_file.
	'''

	TAG = 2

	_hprof_offsets = AutoOffsets(_base.offsets.BODY,
		'SERIAL', 4,
		'CLSID', idoffset(1),
		'STRACE', 4,
		'NAMEID', idoffset(1),
	)

	@property
	def class_name(self):
		'''the name of the loaded class.'''
		nameid = self._hprof_id(self._hproff.NAMEID)
		return self.hprof_file.name(nameid).str

	@property
	def class_id(self):
		'''the ID of the resulting class object; can be used to find it.'''
		return self._hprof_id(self._hproff.CLSID)

	def __str__(self):
		return 'ClassLoad(%s)' % self.class_name
