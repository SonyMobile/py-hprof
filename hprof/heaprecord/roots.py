#!/usr/bin/env python3
#coding=utf8

from .heaprecord import HeapRecord

from ..offset import offset, AutoOffsets, idoffset
from ..errors import RefError

class GcRoot(HeapRecord):
	@property
	def objid(self):
		return self._hprof_id(self._hproff.ID)

	def __len__(self):
		return self._hproff.END

	def _info(self):
		return 'objid=0x%x' % self.objid

	def __str__(self):
		return '%s(%s)' % (type(self).__name__, self._info())

class UnknownRoot(GcRoot):
	HPROF_DUMP_TAG = 0xff
	_hprof_offsets = AutoOffsets(1, 'ID', idoffset(1), 'END')

class GlobalJniRoot(GcRoot):
	HPROF_DUMP_TAG = 0x01
	_hprof_offsets = AutoOffsets(1,
			'ID',     idoffset(1),
			'REFID',  idoffset(1),
			'END')

	@property
	def grefid(self):
		return self._hprof_id(self._hproff.REFID)

	def _info(self):
		return super()._info() + ', grefid=0x%x' % self.grefid

class LocalJniRoot(GcRoot):
	HPROF_DUMP_TAG = 0x02
	_hprof_offsets = AutoOffsets(1,
			'ID',     idoffset(1),
			'STRACE', 4,
			'FRAME',  4,
			'END')

	def _info(self):
		return super()._info() + ' in <func>' # TODO: actually show the function here.

class JavaStackRoot(GcRoot):
	HPROF_DUMP_TAG = 0x03
	_hprof_offsets = AutoOffsets(1,
			'ID',     idoffset(1),
			'THREAD', 4,
			'FRAME',  4,
			'END')

	def _info(self):
		return super()._info() + ' in <func>' # TODO: not <func>

class NativeStackRoot(GcRoot):
	HPROF_DUMP_TAG = 0x04
	_hprof_offsets = AutoOffsets(1,
			'ID',     idoffset(1),
			'THREAD', 4,
			'END')

	def _info(self):
		return super()._info() + ' from thread ???' # TODO: not "???"

class StickyClassRoot(GcRoot):
	HPROF_DUMP_TAG = 0x05
	_hprof_offsets = AutoOffsets(1, 'ID', idoffset(1), 'END')

class ThreadRoot(GcRoot):
	HPROF_DUMP_TAG = 0x08
	_hprof_offsets = AutoOffsets(1,
			'ID',     idoffset(1),
			'THREAD', 4,
			'STRACE', 4,
			'END')

	def _info(self):
		return super()._info() + ' from thread ???' # TODO: actually show the thread here.

class InternedStringRoot(GcRoot):
	HPROF_DUMP_TAG = 0x89
	_hprof_offsets = AutoOffsets(1, 'ID', idoffset(1), 'END')

class VmInternalRoot(GcRoot):
	HPROF_DUMP_TAG = 0x8d
	_hprof_offsets = AutoOffsets(1,
			'ID',    idoffset(1),
			'END')
