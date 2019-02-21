#!/usr/bin/env python3
#coding=utf8

from ..commonrecord import HprofSlice
from ..errors import *

_descendants = {}

def _find_descendants(cls):
	yield cls
	for child in cls.__subclasses__():
		yield from _find_descendants(child)

def _get_record_type(tag):
	try:
		return _descendants[tag]
	except KeyError:
		pass
	# not found; let's see if rebuilding the cache helps (probably not, though)
	_descendants.clear()
	for cls in _find_descendants(HeapRecord):
		ctag = getattr(cls, 'HPROF_DUMP_TAG', None)
		if ctag is not None:
			_descendants[ctag] = cls
	return _descendants[tag]

class HeapRecord(HprofSlice):
	pass

def create(hf, addr):
	tag = hf.read_byte(addr)
	try:
		rtype = _get_record_type(tag)
	except KeyError:
		raise FileFormatError('unknown HeapDump subrecord tag 0x%02x at address 0x%x' % (tag, addr))
	return rtype(hf, addr)

class Allocation(HeapRecord):
	__slots__ = 'hprof_heap',

	@property
	def hprof_id(self):
		return self._hprof_id(self._hproff.ID)
