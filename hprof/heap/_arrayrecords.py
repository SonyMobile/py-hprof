from ._heaprecord import Allocation

from .._errors import FieldNotFoundError
from .._offset import offset, AutoOffsets, idoffset
from .._types import JavaType

class Array(Allocation):
	'''Common operations on array types.

	Members:
	hprof_file -- the HprofFile this array belongs to.
	hprof_addr -- the byte address of this array in hprof_file.
	hprof_heap -- the hprof.Heap this array belongs to.
	'''

	@property
	def length(self):
		'''the number of elements in this array.'''
		return self._hprof_uint(self._hproff.COUNT)

	def __len__(self):
		return self.length

class PrimitiveArray(Array):
	'''An array of primitive values.

	The array can be accessed like a normal python array; `len(arr)`, `arr[ix]`, and `for v in arr`
	works as expected.

	Members:
	hprof_file -- the HprofFile this array belongs to.
	hprof_addr -- the byte address of this array in hprof_file.
	hprof_heap -- the hprof.Heap this array belongs to.
	'''

	HPROF_DUMP_TAG = 0x23

	_hprof_offsets = AutoOffsets(1,
			'ID',     idoffset(1),
			'STRACE', 4,
			'COUNT',  4,
			'TYPE',   1,
			'DATA')

	@property
	def hprof_elem_type(self):
		'''the type of this array's elements, as a JavaType.'''
		return self._hprof_jtype(self._hproff.TYPE)

	@property
	def hprof_class_id(self):
		'''the class ID of this array.'''
		return self.hprof_file.get_class_info(self.hprof_elem_type.name + '[]').class_id

	@property
	def _hprof_len(self):
		return self._hproff.DATA + self.length * self.hprof_elem_type.size(self.hprof_file.idsize)

	def __str__(self):
		content = ', '.join(str(item) for item in self)
		return '%s[%d] {%s}' % (self.hprof_elem_type, self.length, content)

	def __repr__(self):
		return 'PrimitiveArray(type=%s, id=0x%x, length=%d)' % (self.hprof_elem_type, self.hprof_id, self.length)

	def __getitem__(self, ix):
		if 0 <= ix < self.length:
			t = self.hprof_elem_type
			offset = self._hproff.DATA + ix * t.size(self.hprof_file.idsize)
			return self._hprof_jvalue(offset, t)
		else:
			raise IndexError('tried to read element %d in a size %d array' % (ix, self.length))

class ObjectArray(Array):
	'''An array of object references.

	The array can be accessed like a normal python array: `len(arr)`, `arr[ix]`, and `for v in arr`
	works as expected.

	null values will be returned as python None values.

	Members:
	hprof_file -- the HprofFile this record belongs to.
	hprof_addr -- the byte address of this record in hprof_file.
	hprof_heap -- the hprof.Heap this record belongs to.
	'''
	HPROF_DUMP_TAG = 0x22

	_hprof_offsets = AutoOffsets(1,
			'ID',	  idoffset(1),
			'STRACE', 4,
			'COUNT',  4,
			'CLSID',  idoffset(1),
			'DATA')

	@property
	def _hprof_len(self):
		return self._hproff.DATA + self.length * self.hprof_file.idsize

	def __str__(self):
		if self.hprof_heap is None:
			cname = '<UnknownType>[]'
			content = ', '.join('id=0x%x' % self._hprof_item_id(i) for i in range(self.length))
		else:
			cname = self.hprof_class.hprof_name.rsplit('.', 1)[-1]
			content = ', '.join(str(item) for item in self)
		return '%s[%d] {%s}' % (cname[:-2], self.length, content)

	def __repr__(self):
		if self.hprof_heap is None:
			return 'ObjectArray(class_id=0x%x, id=0x%x, length=%d)' % (self.hprof_class_id, self.hprof_id, self.length)
		else:
			return 'ObjectArray(class=%s, id=0x%x, length=%d)' % (self.hprof_class.hprof_name, self.hprof_id, self.length)

	@property
	def hprof_class_id(self):
		'''the class ID of this array.'''
		return self._hprof_id(self._hproff.CLSID)

	def _hprof_item_id(self, ix):
		if 0 <= ix < self.length:
			return self._hprof_id(self._hproff.DATA + ix * self.hprof_file.idsize)
		else:
			raise IndexError('tried to read element %d in a size %d array' % (ix, self.length))

	def __getitem__(self, ix):
		item_id = self._hprof_item_id(ix)
		return self.hprof_heap.dump.get_object(item_id)
