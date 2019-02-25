#!/usr/bin/env python3
#coding=utf8

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
	def name(self):
		nameid = self._hprof_id(self._hproff.NAMEID)
		return self.hprof_file.name(nameid).str

	@property
	def serial(self):
		return self._hprof_uint(self._hproff.SERIAL)

	@property
	def class_id(self):
		return self._hprof_id(self._hproff.CLSID)

	def __str__(self):
		return 'ClassLoad(%s)' % self.name
