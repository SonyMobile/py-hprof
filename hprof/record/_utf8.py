#!/usr/bin/env python3
#coding=utf8

from . import _base
from .._offset import *


class Utf8(_base.Record):
	TAG = 1

	_hprof_offsets = AutoOffsets(_base.offsets.BODY,
		'ID', idoffset(1),
		'STR'
	)

	@property
	def str(self):
		return self._hprof_utf8(self._hproff.STR, self._hprof_len - self._hproff.STR)

	@property
	def id(self):
		return self._hprof_id(self._hproff.ID)

	def __str__(self):
		return self.str
