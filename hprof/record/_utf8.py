# Copyright (C) 2019 Sony Mobile Communications Inc.
# Licensed under the LICENSE

from . import _base
from .._offset import *


class Utf8(_base.Record):
	'''A name declaration record, used for metadata like class/method/field names.

	Members:
	hprof_file -- the HprofFile this record belongs to.
	hprof_addr -- the byte address of this record in hprof_file.
	'''

	TAG = 1

	_hprof_offsets = AutoOffsets(_base.offsets.BODY,
		'ID', idoffset(1),
		'STR'
	)

	@property
	def str(self):
		'''the string value contained in this record.'''
		return self._hprof_utf8(self._hproff.STR, self._hprof_len - self._hproff.STR)

	@property
	def id(self):
		'''The ID of this name.

		Note that this ID is not necessarily in the same namespace as IDs in heap dumps.
		'''
		return self._hprof_id(self._hproff.ID)

	def __str__(self):
		return self.str
