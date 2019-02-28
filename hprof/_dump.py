from ._errors import *
from .heap import *
from ._slotted import Slotted

class Dump(object, metaclass=Slotted):
	'''A single memory dump, usually acquired through hprof.HprofFile.dumps().

	An hprof file may technically contain multiple dumps. A Dump object represents a single memory
	dump, within which object references are valid. Object IDs and references may not work across
	different dumps.

	Note that this library is currently not very well-tested with multiple-dump hprof files.

	Members:
	hf -- the HprofFile this dump belongs to.
	'''

	__slots__ = 'hf', '_heaps', '_current_heap', '_subclass_cache', '_instance_cache'

	def __init__(self, hf):
		self.hf = hf
		self._heaps = {}
		self._current_heap = None
		self._subclass_cache = {}
		self._instance_cache = {}

	def _add_segment(self, seg):
		assert seg.hprof_file is self.hf
		for r in seg.records():
			if type(r) is HeapDumpInfo:
				self._set_curheap(r.type, r.name.str)
			elif isinstance(r, Allocation):
				objid = r.hprof_id
				clsid = r.hprof_class_id
				if clsid not in self._instance_cache:
					self._instance_cache[clsid] = []
				self._instance_cache[clsid].append(r)
				if any(h.has_id(objid) for h in self._heaps.values()):
					raise FileFormatError('duplicate object id 0x%x' % objid)
				self._curheap._add_alloc(objid, r)
				if type(r) is Class:
					superid = r.hprof_super_class_id
					try:
						self._subclass_cache[superid].append(objid)
					except KeyError:
						self._subclass_cache[superid] = [objid]

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
		'''yield all the heaps present in this dump.

		This will normally be just one heap for most targets. Relatively recent Android versions
		may have up to three.'''
		yield from self._heaps.values()

	def get_class(self, class_id_or_name):
		'''return the Class object with the given ID'''
		if type(class_id_or_name) is int:
			clsid = class_id_or_name
			if clsid == 0:
				return None
		else:
			clsid = self.hf.get_class_info(class_id_or_name).class_id
		for h in self._heaps.values():
			try:
				return h._classes[clsid]
			except KeyError:
				pass
		raise ClassNotFoundError('Failed to find class object with id 0x%x' % clsid)

	def get_object(self, objid):
		'''return the object with the given ID

		This includes all kinds: normal instances, class objects, and primitive and object arrays.
		'''
		if objid == 0:
			return None
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

	def _subclasses(self, cls):
		try:
			subids = self._subclass_cache[cls.hprof_id]
		except KeyError:
			return # no known subclasses
		for clsid in subids:
			yield self.get_class(clsid)

	def _descendants(self, out, cls):
		clsid = cls.hprof_id
		out.add(clsid)
		try:
			subids = self._subclass_cache[clsid]
		except KeyError:
			return
		for subid in self._subclass_cache[clsid]:
			self._descendants(out, self.get_class(subid))

	def find_instances(self, class_object_or_name, include_descendants=True):
		'''yield all object instances of the specified class.'''
		if type(class_object_or_name) is str:
			class_object_or_name = self.get_class(class_object_or_name)
		class_ids = set()
		class_ids.add(class_object_or_name.hprof_id)
		if include_descendants:
			self._descendants(class_ids, class_object_or_name)
		for clsid in class_ids:
			try:
				instances = self._instance_cache[clsid]
			except KeyError:
				continue
			yield from instances

class Heap(object, metaclass=Slotted):
	'''A single heap, usually acquired through hprof.Dump.heaps().

	Android's ART maintains several different heaps, which can hold references
	to objects in each other.

	Heaps are mostly handled transparently; you don't have to care which heap an object belongs to.

	Fields:
	dump -- our parent Dump object
	name -- the name of our heap
	type -- an integer used to identify heap types (-1 when no heap info was present)
	'''

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
		'''Check whether this heap contains the specified ID'''
		return objid in self._classes or objid in self._objects

	def objects(self):
		'''yield all objects in this heap.

		Includes all kinds: normal instances, class objects, and primitive and object arrays.
		'''
		yield from self._classes.values()
		yield from self._objects.values()

	def __str__(self):
		return 'Heap(type=%d, name=%s)' % (self.type, self.name)
