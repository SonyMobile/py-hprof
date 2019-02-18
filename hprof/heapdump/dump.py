#!/usr/bin/env python3
#coding=utf8

from ..errors import *
from ..heaprecord import *
from ..immutable import Immutable

from .object import Object

class Dump(Immutable):
	__slots__ = 'hf', '_heaps', '_current_heap'

	def __init__(self, hf):
		self.hf = hf
		self._heaps = {}
		self._current_heap = None

	def _add_segment(self, seg):
		assert seg.hf is self.hf
		for r in seg.records():
			if type(r) is HeapDumpInfo:
				self._set_curheap(r.type, r.name.str)
			elif type(r) is ObjectRecord:
				objid = r.id
				if any(objid in h._objects for h in self._heaps.values()):
					raise FileFormatError('duplicate object id 0x%x' % objid)
				self._curheap._add_object(r)

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

class Heap(Immutable):
	__slots__ = 'dump', 'name', 'type', '_objects'

	def __init__(self, dump, name, heaptype):
		self.dump = dump
		self.name = name
		self.type = heaptype
		self._objects = {}

	def _add_object(self, objrec):
		self._objects[objrec.id] = objrec

	def objects(self):
		for objrec in self._objects.values():
			yield Object(self, objrec)

	def __str__(self):
		return 'Heap(type=%d, name=%s)' % (self.type, self.name)
