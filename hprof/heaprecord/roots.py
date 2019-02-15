#!/usr/bin/env python3
#coding=utf8

from .heaprecord import HeapRecord

from ..offset import offset

class GcRoot(HeapRecord):
	__slots__ = ()

class UnknownRoot(GcRoot):
	__slots__ = ()
	TAG = 0xff

	def __len__(self):
		return offset(1, 1).flatten(self.hf.idsize)
