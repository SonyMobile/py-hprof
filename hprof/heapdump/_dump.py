#!/usr/bin/env python3
#coding=utf8

from .._errors import *
from ..heaprecord import *
from .._slotted import Slotted

class Dump(object, metaclass=Slotted):
	__slots__ = 'hf', '_heaps', '_current_heap'

	def __init__(self, hf):
		self.hf = hf
		self._heaps = {}
		self._current_heap = None

	def _add_segment(self, seg):
		assert seg.hprof_file is self.hf
		for r in seg.records():
			if type(r) is HeapDumpInfo:
				self._set_curheap(r.type, r.name.str)
			elif isinstance(r, Allocation):
				objid = r.hprof_id
				if any(h.has_id(objid) for h in self._heaps.values()):
					raise FileFormatError('duplicate object id 0x%x' % objid)
				self._curheap._add_alloc(objid, r)

	def _set_curheap(self, htype, hname):
		if htype not in self._heaps:
			self._heaps[htype] = Heap(self, hname, htype)
		h = self._heaps[htype]
		self._current_heap = h
		if h.name != hname:
			raise FileFormatError('heap type %d appears with multiple names: %s and %s' % (htype, h.name, hname))

	@property
	def _curheap(self):
		if self._current_heap is None:
			self._set_curheap(-1, '<unspecified>')
		return self._current_heap

	def heaps(self):
		yield from self._heaps.values()

	def get_class(self, clsid):
		for h in self._heaps.values():
			try:
				return h._classes[clsid]
			except KeyError:
				pass
		raise ClassNotFoundError('Failed to find class object with id 0x%x' % clsid)

	def get_object(self, objid):
		for h in self._heaps.values():
			try:
				return h._objects[objid]
			except KeyError:
				pass
			try:
				return h._classes[objid]
			except KeyError:
				pass
		raise RefError('Failed to find object with id 0x%x' % objid)

class Heap(object, metaclass=Slotted):
	__slots__ = 'dump', 'name', 'type', '_objects', '_classes'

	def __init__(self, dump, name, heaptype):
		self.dump = dump
		self.name = name
		self.type = heaptype
		self._objects = {} # id -> object record (does not include classes)
		self._classes = {} # id -> class record

	def _add_alloc(self, objid, record):
		record.hprof_heap = self
		if type(record) is Class:
			self._classes[objid] = record
		else:
			self._objects[objid] = record

	def has_id(self, objid):
		return objid in self._classes or objid in self._objects

	def objects(self):
		yield from self._classes.values()
		yield from self._objects.values()

	def __str__(self):
		return 'Heap(type=%d, name=%s)' % (self.type, self.name)
