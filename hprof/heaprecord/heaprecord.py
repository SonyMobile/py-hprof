#!/usr/bin/env python3
#coding=utf8

from ..commonrecord import CommonRecord
from ..errors import *

def _descendants(cls):
	yield cls
	for child in cls.__subclasses__():
		yield from _descendants(child)

class HeapRecord(CommonRecord):
	__slots__ = ()

	@staticmethod
	def create(hf, addr):
		from .roots import UnknownRoot
		tag = hf.read_byte(addr)
		# TODO: some form of caching here might not be a bad idea.
		rtype = None
		for candidate in _descendants(HeapRecord):
			if getattr(candidate, 'TAG', None) == tag:
				rtype = candidate
		if rtype is None:
			raise FileFormatError('unknown HeapDump subrecord tag 0x%02x' % tag)
		return rtype(hf, addr)