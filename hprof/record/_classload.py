from . import _base
from .._offset import *

class ClassLoad(_base.Record):
	TAG = 2

	_hprof_offsets = AutoOffsets(_base.offsets.BODY,
		'SERIAL', 4,
		'CLSID', idoffset(1),
		'STRACE', 4,
		'NAMEID', idoffset(1),
	)

	@property
	def class_name(self):
		nameid = self._hprof_id(self._hproff.NAMEID)
		return self.hprof_file.name(nameid).str

	@property
	def class_id(self):
		return self._hprof_id(self._hproff.CLSID)

	def __str__(self):
		return 'ClassLoad(%s)' % self.class_name
