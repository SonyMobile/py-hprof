#!/usr/bin/env python3
#coding=utf8

from . import base
from ..offset import *


class Utf8(base.Record):
	TAG = 1

	_hprof_offsets = AutoOffsets(base.offsets.BODY,
		'ID', idoffset(1),
		'STR'
	)

	@property
	def str(self):
		return self._hprof_utf8(self._hproff.STR, len(self) - self._hproff.STR)

	@property
	def id(self):
		return self._hprof_id(self._hproff.ID)

	def __str__(self):
		return self.str
