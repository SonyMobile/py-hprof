from unittest import TestCase

import hprof

def everything(above, thing):
	yield above
	if type(thing) in (str, int, property, hprof.JavaType):
		return
	if isinstance(thing, type) and issubclass(thing, hprof.Error):
		return
	try:
		if thing.__package__ is not None and 'hprof' not in thing.__package__:
			return
	except AttributeError:
		pass
	try:
		if thing.__module__ is not None and 'hprof' not in thing.__module__:
			return
	except AttributeError:
		pass

	for name in dir(thing):
		if name.startswith('_'):
			continue
		yield from everything(above + '.' + name, getattr(thing, name))

def expanded(above, collection):
	yield above
	for name in collection:
		fullname = above + '.' + name
		if type(collection) is dict:
			yield from expanded(fullname, collection[name])
		else:
			yield fullname

def hprofslice(*fields):
	return tuple(fields) + ('hprof_file', 'hprof_addr')

def baserecord(*fields):
	return hprofslice('rawbody', 'timestamp', 'relative_timestamp', *fields)

def record(*fields):
	return baserecord('TAG', *fields)

def rootrecord(*fields):
	return hprofslice('HPROF_DUMP_TAG', 'objid', *fields)

def heap(*fields):
	return hprofslice('hprof_id', 'hprof_class_id', 'hprof_class', 'hprof_heap', *fields)

def heapobj(*fields):
	return heap('HPROF_DUMP_TAG', *fields)

class TestApiSurface(TestCase):
	def setUp(self):
		self.expected = sorted(expanded('hprof', {
			'open': (),
			'HprofFile': (
				'close', 'records', 'dumps', 'name',
				'read_byte', 'read_ushort', 'read_uint',
				'read_short', 'read_int', 'read_long',
				'read_boolean', 'read_char', 'read_float', 'read_double',
				'read_id', 'read_jtype', 'read_jvalue',
				'read_bytes', 'read_ascii', 'read_utf8',
				'get_class_info',
			),
			'JavaType': ('object', 'boolean', 'char', 'float', 'double', 'byte', 'short', 'int', 'long'),

			'Dump': ('hf', 'get_class', 'get_object', 'heaps'),
			'Heap': ('dump', 'has_id', 'name', 'type', 'objects'),

			'Error': (),
			'RefError': (),
			'ClassNotFoundError': (),
			'EofError': (),
			'FileFormatError': (),
			'FieldNotFoundError': (),

			'record': {
				'create': (),
				'Record': baserecord(),

				'Utf8': record('str', 'id'),
				'ClassLoad': record('class_name', 'class_id'),
				'HeapDumpSegment': record('records'),
				'HeapDumpEnd': record(),
				'Unhandled': baserecord(),
			},
			'heap': {
				'create': (),
				'HeapRecord': hprofslice(),
				'HeapDumpInfo': hprofslice('HPROF_DUMP_TAG', 'name', 'type'),

				'GcRoot': hprofslice('objid'),
				'UnknownRoot': rootrecord(),
				'ThreadRoot': rootrecord(),
				'GlobalJniRoot': rootrecord('grefid'),
				'LocalJniRoot': rootrecord(),
				'NativeStackRoot': rootrecord(),
				'StickyClassRoot': rootrecord(),
				'MonitorRoot': rootrecord(),
				'VmInternalRoot': rootrecord(),
				'JavaStackRoot': rootrecord(),
				'InternedStringRoot': rootrecord(),

				'Allocation': heap(),
				'Class': heapobj('hprof_name', 'hprof_super_class_id', 'hprof_instance_size', 'hprof_instance_fields', 'hprof_static_fields'),
				'Object': heapobj(),
				'Array': heap('length'),
				'ObjectArray': heapobj('length'),
				'PrimitiveArray': heapobj('length', 'hprof_elem_type'),

				'FieldDecl': hprofslice('name', 'type'),
				'StaticField': hprofslice('decl', 'value'),
			},
		}))

	def test_api_surface(self):
		self.maxDiff = None
		self.assertCountEqual(everything('hprof', hprof), self.expected)

	def test_api_documented(self):
		class Unused(object):
			__slots__ = 'member'
		member_descriptor = type(Unused.member)
		for name in self.expected:
			thing = eval(name)
			if type(thing) is member_descriptor:
				# can't be documented directly; check that it is present in its parent.
				parent, member = name.rsplit('.', 1)
				thing = eval(parent)
				self.assertIsNotNone(thing.__doc__, msg=name + '.__doc__')
				pattern = '\n[\t ]*%s -- ' % member
				self.assertRegex(thing.__doc__, pattern, msg='%s not documented in %s' % (member, parent))
			else:
				self.assertIsNotNone(thing.__doc__, msg=name + '.__doc__')
				self.assertNotEqual(thing.__doc__.strip(), '', msg=name + '.__doc__')
