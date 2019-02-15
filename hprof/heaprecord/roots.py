#!/usr/bin/env python3
#coding=utf8

from .heaprecord import HeapRecord

from ..offset import offset

class UnknownRoot(HeapRecord):
	TAG = 0xff

	@property
	def id(self):
		return self._read_id(1)

	def __len__(self):
		return offset(1, 1).flatten(self.hf.idsize)
