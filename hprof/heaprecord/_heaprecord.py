#!/usr/bin/env python3
#coding=utf8

from .._commonrecord import HprofSlice
from .._errors import *
from .._types import JavaType

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

	def __init__(self, hf, addr):
		super().__init__(hf, addr)
		self.hprof_heap = None

	@property
	def hprof_id(self):
		return self._hprof_id(self._hproff.ID)

	@property
	def hprof_class(self):
		return self.hprof_heap.dump.get_class(self.hprof_class_id)

	@property
	def hprof_class_id(self):
		raise NotImplementedError(type(self)) # pragma: no cover

	def __getattr__(self, name):
		return self.__getitem__(name)

	def __getitem__(self, name):
		cls = self.hprof_class
		try:
			jtype, offset = cls._hprof_instance_field_lookup(name)
		except FieldNotFoundError:
			try:
				return cls[name]
			except FieldNotFoundError as e:
				e.type = 'static or instance'
				raise
		value = self._hprof_jvalue(self._hproff.DATA + offset, jtype)
		if jtype == JavaType.object:
			return self.hprof_heap.dump.get_object(value)
		else:
			return value
