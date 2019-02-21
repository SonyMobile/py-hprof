#!/usr/bin/env python3
#coding=utf8

from . import base
from ..offset import *

class ClassLoad(base.Record):
	TAG = 2

	_hprof_offsets = AutoOffsets(base.offsets.BODY,
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

	def __str__(self):
		return 'ClassLoad(%s)' % self.name
