import hprof

from .error import *

from . import jtype

from collections import OrderedDict

class DeferredRef(int):
	__slots__ = ()

record_parsers = {}

# TODO: useful stuff in these.
record_parsers[0xff] = lambda f, h, r: (r.id())
record_parsers[0x01] = lambda f, h, r: (r.id(), r.id())
record_parsers[0x02] = lambda f, h, r: (r.id(), r.u4(), r.u4())
record_parsers[0x03] = lambda f, h, r: (r.id(), r.u4(), r.u4())
record_parsers[0x04] = lambda f, h, r: (r.id(), r.u4())
record_parsers[0x05] = lambda f, h, r: (r.id())
record_parsers[0x06] = lambda f, h, r: (r.id(), r.u4())
record_parsers[0x07] = lambda f, h, r: (r.id())
record_parsers[0x08] = lambda f, h, r: (r.id(), r.u4(), r.u4())
record_parsers[0x89] = lambda f, h, r: (r.id())
record_parsers[0x8b] = lambda f, h, r: (r.id())
record_parsers[0x8d] = lambda f, h, r: (r.id())
record_parsers[0x8e] = lambda f, h, r: (r.id(), r.u4(), r.u4())

record_parsers[0xfe] = lambda f, h, r: (r.u4(), r.id())

def parse_class(hf, heap, reader):
	objid   = reader.id()
	strace  = reader.u4()
	superid = reader.id()
	loader  = reader.id()
	signer  = reader.id()
	protdom = reader.id()
	res1    = reader.id()
	res2    = reader.id()
	objsize = reader.u4()

	if objid in heap:
		raise FormatError('duplicate object id 0x%x' % objid)

	nconstants = reader.u2()
	for i in range(nconstants):
		reader.u2()
		t = reader.jtype()
		t.read(reader)

	staticattrs = {}
	nstatic = reader.u2()
	for i in range(nstatic):
		nameid = reader.id()
		name = hf.names[nameid]
		t = reader.jtype()
		val = t.read(reader)
		staticattrs[name] = val

	instanceattrs = OrderedDict()
	ninstance = reader.u2()
	for i in range(ninstance):
		nameid = reader.id()
		name = hf.names[nameid]
		vtype = reader.jtype()
		instanceattrs[name] = vtype

	load = hf.classloads_by_id[objid]
	if superid == 0:
		supercls = None
	else:
		try:
			supercls = heap[superid]
		except KeyError:
			if superid not in heap._deferred_classes:
				heap._deferred_classes[superid] = []
			heap._deferred_classes[superid].append((objid, load.class_name, staticattrs, instanceattrs))
			return

	def create(objid, cname, supercls, staticattrs, instanceattrs):
		clsname, cls = hprof.heap._create_class(heap.classtree, cname, supercls, staticattrs, instanceattrs)
		heap._instances[cls] = []
		if clsname not in heap.classes:
			heap.classes[clsname] = []
		heap.classes[clsname].append(cls)
		heap[objid] = cls
		if objid in heap._deferred_classes:
			deferred = heap._deferred_classes.pop(objid)
			for objid, cname, staticattrs, instanceattrs in deferred:
				create(objid, cname, cls, staticattrs, instanceattrs)

	create(objid, load.class_name, supercls, staticattrs, instanceattrs)
record_parsers[0x20] = parse_class

def parse_instance(hf, heap, reader):
	objid = reader.id()
	strace = reader.u4()
	clsid = reader.id()
	remaining = reader.u4()
	bytes = reader.bytes(remaining)
	heap._deferred_objects.append((objid, strace, clsid, bytes))
record_parsers[0x21] = parse_instance

def create_instances(heap, idsize, progress):
	from ._parsing import PrimitiveReader
	until_report = 0
	for ix, (objid, strace, clsid, bytes) in enumerate(heap._deferred_objects):
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
					for ix, (aname, atype)
					in enumerate(cls._hprof_ifields.items())
			)
			assert len(vals) == len(cls._hprof_ifieldix), (len(vals), len(cls._hprof_ifieldix))
			cls._hprof_ifieldvals.__set__(obj, vals)
			cls, = cls.__bases__
		assert reader._pos == len(bytes), (reader._pos, len(bytes))
		heap._instances[exactcls].append(obj)
		heap[objid] = obj
	heap._deferred_objects.clear()

def parse_object_array(hf, heap, reader):
	objid = reader.id()
	strace = reader.u4()
	length = reader.u4()
	clsid = reader.id()
	elems = tuple(reader.id() for ix in range(length))
	heap._deferred_objarrays.append((objid, strace, clsid, elems))
record_parsers[0x22] = parse_object_array

def create_objarrays(heap, progress):
	until_report = 0
	for ix, (objid, strace, clsid, elems) in enumerate(heap._deferred_objarrays):
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
	objid  = reader.id()
	strace = reader.u4()
	length = reader.u4()
	t = reader.jtype()
	data = reader.bytes(length * t.size)
	data = hprof.heap._DeferredArrayData(t, data)
	heap._deferred_primarrays.append((objid, strace, data))
record_parsers[0x23] = parse_primitive_array

def create_primarrays(heap, progress):
	until_report = 0
	for ix, (objid, strace, data) in enumerate(heap._deferred_primarrays):
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
			parser = record_parsers[rtype]
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
					for ix, (aname, atype) in enumerate(cls._hprof_ifields.items())
				)
				cls._hprof_ifieldvals.__set__(obj, new)
				cls, = cls.__bases__
	if progresscb:
		progresscb(len(heap))
