# Copyright (C) 2019 Snild Dolkow
# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

'''
Parses the content of hprof files' heap dump records.
'''

from . import heap as hprof_heap
from ._parsing import jtype
from .error import FormatError, MissingObject, UnexpectedEof

class DeferredRef(int):
	''' Used to seperate int values from ref values that should be resolved when
	the heap is complete. Not expected to be used by outsiders. '''
	__slots__ = ()

RECORD_PARSERS = {}

# TODO: useful stuff in these.
RECORD_PARSERS[0xff] = lambda f, h, r: (r.id())
RECORD_PARSERS[0x01] = lambda f, h, r: (r.id(), r.id())
RECORD_PARSERS[0x02] = lambda f, h, r: (r.id(), r.u4(), r.u4())
RECORD_PARSERS[0x03] = lambda f, h, r: (r.id(), r.u4(), r.u4())
RECORD_PARSERS[0x04] = lambda f, h, r: (r.id(), r.u4())
RECORD_PARSERS[0x05] = lambda f, h, r: (r.id())
RECORD_PARSERS[0x06] = lambda f, h, r: (r.id(), r.u4())
RECORD_PARSERS[0x07] = lambda f, h, r: (r.id())
RECORD_PARSERS[0x08] = lambda f, h, r: (r.id(), r.u4(), r.u4())
RECORD_PARSERS[0x89] = lambda f, h, r: (r.id())
RECORD_PARSERS[0x8b] = lambda f, h, r: (r.id())
RECORD_PARSERS[0x8d] = lambda f, h, r: (r.id())
RECORD_PARSERS[0x8e] = lambda f, h, r: (r.id(), r.u4(), r.u4())

RECORD_PARSERS[0xfe] = lambda f, h, r: (r.u4(), r.id())

def parse_class(hf, heap, reader):
	''' Reads in one class instance, adds it to the heap. '''
	objid   = reader.id()
	_       = reader.u4() # stacktrace id
	superid = reader.id()
	_       = reader.id() # loader
	_       = reader.id() # signer
	_       = reader.id() # protection domain
	_       = reader.id() # reserved 1
	_       = reader.id() # reserved 2
	_       = reader.u4() # object size

	if objid in heap:
		raise FormatError('duplicate object id 0x%x' % objid)

	nconstants = reader.u2()
	for _ in range(nconstants):
		reader.u2()
		t = reader.jtype()
		t.read(reader)

	staticattrs = {}
	nstatic = reader.u2()
	for _ in range(nstatic):
		nameid = reader.id()
		name = hf.names[nameid]
		t = reader.jtype()
		val = t.read(reader)
		staticattrs[name] = val

	namelist = []
	typelist = []
	ninstance = reader.u2()
	for _ in range(ninstance):
		nameid = reader.id()
		name = hf.names[nameid]
		vtype = reader.jtype()
		namelist.append(name)
		typelist.append(vtype)
	iattr_names = tuple(namelist)
	iattr_types = tuple(typelist)

	load = hf.classloads_by_id[objid]
	if superid == 0:
		supercls = None
	else:
		try:
			supercls = heap[superid]
		except KeyError:
			if superid not in heap._deferred_classes:
				heap._deferred_classes[superid] = []
			heap._deferred_classes[superid].append((objid, load.class_name, staticattrs, iattr_names, iattr_types))
			return

	def create(objid, cname, supercls, staticattrs, iattr_names, iattr_types):
		''' Creates a class instance. There may be deferred classes waiting for
		this one; create those too. '''
		clsname, cls = hprof_heap._create_class(heap.classtree, cname, supercls, staticattrs, iattr_names, iattr_types)
		heap._instances[cls] = []
		if clsname not in heap.classes:
			heap.classes[clsname] = []
		heap.classes[clsname].append(cls)
		heap[objid] = cls
		if objid in heap._deferred_classes:
			deferred = heap._deferred_classes.pop(objid)
			for objid, cname, staticattrs, iattr_names, iattr_types in deferred:
				create(objid, cname, cls, staticattrs, iattr_names, iattr_types)

	create(objid, load.class_name, supercls, staticattrs, iattr_names, iattr_types)
RECORD_PARSERS[0x20] = parse_class

def parse_instance(hf, heap, reader):
	''' Reads in one object instance, adds it to the queue. '''
	del hf # unused
	objid = reader.id()
	strace = reader.u4()
	clsid = reader.id()
	remaining = reader.u4()
	raw_attrs = reader.bytes(remaining)
	heap._deferred_objects.append((objid, strace, clsid, raw_attrs))
RECORD_PARSERS[0x21] = parse_instance

def create_instances(heap, idsize, progress):
	''' Creates all the queued object instances, adds them to the heap. '''
	from ._parsing import PrimitiveReader
	until_report = 0
	for ix, (objid, _, clsid, raw_attrs) in enumerate(heap._deferred_objects):
		if until_report == 0:
			until_report = 4096
			progress(ix)
		until_report -= 1
		reader = PrimitiveReader(raw_attrs, idsize)
		exactcls = cls = heap[clsid]
		obj = cls(objid)
		while cls is not hprof_heap.JavaObject:
			vals = tuple(
					atype.read(reader)
					for ix, atype
					in enumerate(cls._hprof_ifieldtypes)
			)
			assert len(vals) == len(cls._hprof_ifieldix), (len(vals), len(cls._hprof_ifieldix))
			cls._hprof_ifieldvals.__set__(obj, vals)
			cls, = cls.__bases__
		assert reader._pos == len(raw_attrs), (reader._pos, len(raw_attrs))
		heap._instances[exactcls].append(obj)
		heap[objid] = obj
	heap._deferred_objects.clear()

def parse_object_array(hf, heap, reader):
	''' Reads in one object array, adds it to the queue. '''
	del hf # unused
	objid = reader.id()
	strace = reader.u4()
	length = reader.u4()
	clsid = reader.id()
	elems = tuple(reader.id() for ix in range(length))
	heap._deferred_objarrays.append((objid, strace, clsid, elems))
RECORD_PARSERS[0x22] = parse_object_array

def create_objarrays(heap, progress):
	''' Creates all the queued object arrays, adds them to the heap. '''
	until_report = 0
	for ix, (objid, _, clsid, elems) in enumerate(heap._deferred_objarrays):
		if until_report == 0:
			until_report = 4096
			progress(ix)
		until_report -= 1
		cls = heap[clsid]
		arr = cls(objid, elems)
		heap._instances[cls].append(arr)
		heap[objid] = arr
	heap._deferred_objarrays.clear()

def parse_primitive_array(hf, heap, reader):
	''' Reads in one primitive array, adds it to the queue. '''
	del hf # unused
	objid  = reader.id()
	strace = reader.u4()
	length = reader.u4()
	t = reader.jtype()
	data = reader.bytes(length * t.size)
	data = hprof_heap._DeferredArrayData(t, data)
	heap._deferred_primarrays.append((objid, strace, data))
RECORD_PARSERS[0x23] = parse_primitive_array

def create_primarrays(heap, progress):
	''' Creates all the queued primitive arrays, adds them to the heap. '''
	until_report = 0
	for ix, (objid, _, data) in enumerate(heap._deferred_primarrays):
		if until_report == 0:
			until_report = 4096
			progress(ix)
		until_report -= 1
		t = data.jtype
		clsname = t.name + '[]'
		assert clsname in heap.classes, 'class %s not found' % clsname
		classes = heap.classes[clsname]
		assert len(classes) == 1, 'there are %d classes named %s' % (len(classes), clsname)
		cls, = classes
		# TODO: speed: the class lookup could be done once per array type
		arr = cls(objid, data)
		heap._instances[cls].append(arr)
		heap[objid] = arr
	heap._deferred_primarrays.clear()

def parse_heap(hf, heap, reader, progresscb):
	''' parse a heap dump or heap dump segment '''
	lastreport = 0
	while True:
		try:
			rtype = reader.u1()
		except UnexpectedEof:
			break # nope, it's a normal eof
		if progresscb and reader._pos - lastreport >= 1 << 20:
			lastreport = reader._pos
			progresscb(lastreport)
		try:
			parser = RECORD_PARSERS[rtype]
		except KeyError as e:
			# impossible to handle; we don't know how long this record type is.
			raise FormatError('unrecognized heap record type 0x%x' % rtype) from e
		parser(hf, heap, reader)

def resolve_heap_references(heap, progresscb):
	''' Concretize all heap references from addresses to actual object refs. '''
	def lookup(addr):
		''' return the object at addr, or None if addr is 0. '''
		if not addr:
			return None
		try:
			return heap[addr]
		except KeyError as e:
			raise MissingObject(hex(addr)) from e

	lastreport = 0
	if progresscb:
		progresscb(0)
	for progress, obj in enumerate(heap.values()):
		if progresscb and progress - lastreport >= 10000:
			progresscb(progress)
			lastreport = progress
		cls = type(obj)
		if isinstance(obj, hprof_heap.JavaArray):
			# it's an array; is it an *object* array?
			old = obj._hprof_array_data
			# TODO: this check is probably a bit too fragile
			if not isinstance(old, hprof_heap._DeferredArrayData):
				obj._hprof_array_data = tuple(lookup(addr) for addr in old)
		elif isinstance(obj, hprof_heap.JavaClass):
			for name, val in obj._hprof_sfields.items():
				if isinstance(val, DeferredRef):
					obj._hprof_sfields[name] = lookup(val)
		else:
			# TODO: if/when we have fast per-class instance lookups, it may be faster to do
			#       this one class at a time, rather than walking the hierarchy of each obj
			while cls is not hprof_heap.JavaObject:
				old = cls._hprof_ifieldvals.__get__(obj)
				new = tuple(
					lookup(old[ix]) if atype is jtype.object else old[ix]
					for ix, atype in enumerate(cls._hprof_ifieldtypes)
				)
				cls._hprof_ifieldvals.__set__(obj, new)
				cls, = cls.__bases__
	if progresscb:
		progresscb(len(heap))
