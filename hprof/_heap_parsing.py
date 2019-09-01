import hprof.heap

from .error import *

record_parsers = {}

# TODO: useful stuff in these.
record_parsers[0xff] = lambda h, r: (r.id())
record_parsers[0x01] = lambda h, r: (r.id(), r.id())
record_parsers[0x02] = lambda h, r: (r.id(), r.u(4), r.u(4))
record_parsers[0x03] = lambda h, r: (r.id(), r.u(4), r.u(4))
record_parsers[0x04] = lambda h, r: (r.id(), r.u(4))
record_parsers[0x05] = lambda h, r: (r.id())
record_parsers[0x06] = lambda h, r: (r.id(), r.u(4))
record_parsers[0x07] = lambda h, r: (r.id())
record_parsers[0x08] = lambda h, r: (r.id(), r.u(4), r.u(4))

def parse_class(heap, reader):
	reader.id()
	reader.u(4)
	reader.id()
	reader.id()
	reader.id()
	reader.id()
	reader.id()
	reader.id()
	reader.u(4)

	nconstants = reader.u(2)
	for i in range(nconstants):
		reader.u(2)
		t = reader.jtype()
		reader.jval(t)

	nstatic = reader.u(2)
	for i in range(nstatic):
		reader.id()
		t = reader.jtype()
		reader.jval(t)

	ninstance = reader.u(2)
	for i in range(ninstance):
		reader.id()
		reader.jtype()
record_parsers[0x20] = parse_class

def parse_instance(heap, reader):
	reader.id()
	reader.u(4)
	reader.id()
	remaining = reader.u(4)
	reader.bytes(remaining)
record_parsers[0x21] = parse_instance

def parse_object_array(heap, reader):
	reader.id()
	reader.u(4)
	length = reader.u(4)
	reader.id()
	for i in range(length):
		reader.id()
record_parsers[0x22] = parse_object_array

def parse_primitive_array(heap, reader):
	reader.id()
	reader.u(4)
	length = reader.u(4)
	t = reader.jtype()
	for i in range(length):
		reader.jval(t)
record_parsers[0x23] = parse_primitive_array

def parse_heap(heap, reader):
	while True:
		try:
			rtype = reader.u(1)
		except UnexpectedEof:
			break # nope, it's a normal eof
		try:
			parser = record_parsers[rtype]
		except KeyError as e:
			# impossible to handle; we don't know how long this record type is.
			raise FormatError('unrecognized heap record type 0x%x' % rtype) from e
		parser(heap, reader)

def resolve_heap_references(heap):
	pass
