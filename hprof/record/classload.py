#!/usr/bin/env python3
#coding=utf8

from . import base
from ..offset import *

class ClassLoad(base.Record):
	TAG = 2

	_offsets = AutoOffsets(base.offsets.BODY,
		'SERIAL', 4,
		'CLSID', idoffset(1),
		'STRACE', 4,
		'NAMEID', idoffset(1),
	)

	@property
	def name(self):
		nameid = self._read_id(self._off.NAMEID)
		return self.hf.name(nameid).str

	@property
	def serial(self):
		return self._read_uint(self._off.SERIAL)

	def __str__(self):
		return 'ClassLoad(%s)' % self.name
