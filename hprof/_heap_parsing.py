# Copyright (C) 2019 Snild Dolkow
# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

import hprof

from .error import *

from . import jtype

class DeferredRef(int):
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

	iattr_names = []
	iattr_types = []
	ninstance = reader.u2()
	for _ in range(ninstance):
		nameid = reader.id()
		name = hf.names[nameid]
		vtype = reader.jtype()
		iattr_names.append(name)
		iattr_types.append(vtype)
	iattr_names = tuple(iattr_names)
	iattr_types = tuple(iattr_types)

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
		clsname, cls = hprof.heap._create_class(heap.classtree, cname, supercls, staticattrs, iattr_names, iattr_types)
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
	del hf # unused
	objid = reader.id()
	strace = reader.u4()
	clsid = reader.id()
	remaining = reader.u4()
	bytes = reader.bytes(remaining)
	heap._deferred_objects.append((objid, strace, clsid, bytes))
RECORD_PARSERS[0x21] = parse_instance

def create_instances(heap, idsize, progress):
	from ._parsing import PrimitiveReader
	until_report = 0
	for ix, (objid, _, clsid, bytes) in enumerate(heap._deferred_objects):
		if until_report == 0:
			until_report = 4096
			progress(ix)
		until_report -= 1
		reader = PrimitiveReader(bytes, idsize)
		exactcls = cls = heap[clsid]
		obj = cls(objid)
		while cls is not hprof.heap.JavaObject:
			vals = tuple(
					atype.read(reader)
					for ix, atype
					in enumerate(cls._hprof_ifieldtypes)
			)
			assert len(vals) == len(cls._hprof_ifieldix), (len(vals), len(cls._hprof_ifieldix))
			cls._hprof_ifieldvals.__set__(obj, vals)
			cls, = cls.__bases__
		assert reader._pos == len(bytes), (reader._pos, len(bytes))
		heap._instances[exactcls].append(obj)
		heap[objid] = obj
	heap._deferred_objects.clear()

def parse_object_array(hf, heap, reader):
	del hf # unused
	objid = reader.id()
	strace = reader.u4()
	length = reader.u4()
	clsid = reader.id()
	elems = tuple(reader.id() for ix in range(length))
	heap._deferred_objarrays.append((objid, strace, clsid, elems))
RECORD_PARSERS[0x22] = parse_object_array

def create_objarrays(heap, progress):
	until_report = 0
	for ix, (objid, _, clsid, elems) in enumerate(heap._deferred_objarrays):
		if until_report == 0:
			until_report = 4096
			progress(ix)
		until_report -= 1
		cls = heap[clsid]
		arr = cls(objid)
		arr._hprof_array_data = elems
		heap._instances[cls].append(arr)
		heap[objid] = arr
	heap._deferred_objarrays.clear()

def parse_primitive_array(hf, heap, reader):
	del hf # unused
	objid  = reader.id()
	strace = reader.u4()
	length = reader.u4()
	t = reader.jtype()
	data = reader.bytes(length * t.size)
	data = hprof.heap._DeferredArrayData(t, data)
	heap._deferred_primarrays.append((objid, strace, data))
RECORD_PARSERS[0x23] = parse_primitive_array

def create_primarrays(heap, progress):
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
		arr = cls(objid)
		arr._hprof_array_data = data
		heap._instances[cls].append(arr)
		heap[objid] = arr
	heap._deferred_primarrays.clear()

def parse_heap(hf, heap, reader, progresscb):
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
	def lookup(addr):
		if not addr:
			return None
		try:
			return heap[addr]
		except KeyError as e:
			raise hprof.error.MissingObject(hex(addr)) from e

	lastreport = 0
	if progresscb:
		progresscb(0)
	for progress, obj in enumerate(heap.values()):
		if progresscb and progress - lastreport >= 10000:
			progresscb(progress)
			lastreport = progress
		cls = type(obj)
		if isinstance(obj, hprof.heap.JavaArray):
			# it's an array; is it an *object* array?
			old = obj._hprof_array_data
			# TODO: this check is probably a bit too fragile
			if type(old) is not hprof.heap._DeferredArrayData:
				obj._hprof_array_data = tuple(lookup(addr) for addr in old)
		elif isinstance(obj, hprof.heap.JavaClass):
			for name, val in obj._hprof_sfields.items():
				if type(val) is DeferredRef:
					obj._hprof_sfields[name] = lookup(val)
		else:
			# TODO: if/when we have fast per-class instance lookups, it may be faster to do
			#       this one class at a time, rather than walking the hierarchy of each obj
			while cls is not hprof.heap.JavaObject:
				old = cls._hprof_ifieldvals.__get__(obj)
				new = tuple(
					lookup(old[ix]) if atype is hprof.jtype.object else old[ix]
					for ix, atype in enumerate(cls._hprof_ifieldtypes)
				)
				cls._hprof_ifieldvals.__set__(obj, new)
				cls, = cls.__bases__
	if progresscb:
		progresscb(len(heap))
