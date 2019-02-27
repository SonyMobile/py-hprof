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
	'''Common operations for records internal to Dump records.

	Members:
	hprof_file -- the HprofFile this record belongs to.
	hprof_addr -- the byte address of this record in hprof_file.
	'''

def create(hf, addr):
	'''create a HeapRecord based on the tag and data found at addr.

	You'll probably be better off getting them through hprof.Heap.objects() or hprof.Dump.records().
	'''
	tag = hf.read_byte(addr)
	try:
		rtype = _get_record_type(tag)
	except KeyError:
		raise FileFormatError('unknown HeapDump subrecord tag 0x%02x at address 0x%x' % (tag, addr))
	return rtype(hf, addr)

class Allocation(HeapRecord):
	'''Common operations for heap objects in a dump. This includes all sorts of heap allocations:
	normal objects, class objects, and both primitive and object arrays.

	Members:
	hprof_file -- the HprofFile this object belongs to.
	hprof_addr -- the byte address of this object in hprof_file.
	hprof_heap -- the hprof.Heap this object belongs to.
	'''


	__slots__ = 'hprof_heap',

	def __init__(self, hf, addr):
		super().__init__(hf, addr)
		self.hprof_heap = None

	@property
	def hprof_id(self):
		'''this object's ID on the heap.'''
		return self._hprof_id(self._hproff.ID)

	@property
	def hprof_class(self):
		'''this object's class.'''
		return self.hprof_heap.dump.get_class(self.hprof_class_id)

	@property
	def hprof_class_id(self):
		'''the ID of this object's class.'''
		raise NotImplementedError(type(self)) # pragma: no cover

	def hprof_instanceof(self, cls):
		'''return True if this object is an instance of cls; similar to Java's instanceof.

		Note: this function returns what the hprof file specifies. For example, a String array
		should technically be an instance of Object[], but the hprof may declare String[] to be a
		direct subclass of Object.
		'''
		return self.hprof_class.hprof_descendantof(cls)

	def __getattr__(self, name):
		cls = self.hprof_class
		try:
			jtype, offset = cls._hprof_instance_field_lookup(name)
		except FieldNotFoundError:
			try:
				return getattr(cls, name)
			except FieldNotFoundError as e:
				e.type = 'static or instance'
				raise
		value = self._hprof_jvalue(self._hproff.DATA + offset, jtype)
		if jtype == JavaType.object:
			return self.hprof_heap.dump.get_object(value)
		else:
			return value
