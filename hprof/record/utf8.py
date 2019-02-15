#!/usr/bin/env python3
#coding=utf8

from . import base
from ..offset import *

offsets = AutoOffsets(base.offsets.BODY,
	'ID', idoffset(1),
	'STR'
)

class Utf8(base.Record):
	__slots__ = ()
	TAG = 1

	@property
	def str(self):
		return self._read_utf8(offsets.STR, len(self) - offsets.STR)

	@property
	def id(self):
		return self._read_id(offsets.ID)

	def __str__(self):
		return self.str
