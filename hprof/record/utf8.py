#!/usr/bin/env python3
#coding=utf8

from . import base
from ..offset import *


class Utf8(base.Record):
	TAG = 1

	_offsets = AutoOffsets(base.offsets.BODY,
		'ID', idoffset(1),
		'STR'
	)

	@property
	def str(self):
		return self._read_utf8(self._off.STR, len(self) - self._off.STR)

	@property
	def id(self):
		return self._read_id(self._off.ID)

	def __str__(self):
		return self.str
