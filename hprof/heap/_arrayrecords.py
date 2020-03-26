# Copyright (C) 2019 Sony Mobile Communications Inc.
# Licensed under the LICENSE

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

	>>> shortarray # doctest: +ELLIPSIS
	PrimitiveArray(type=short, id=0x..., length=2)
	>>> print(shortarray)
	short[2] {50, 10}
	>>> [x + 3 for x in shortarray]
	[53, 13]
	>>> shortarray[1]
	10
	>>> len(shortarray)   # python-style
	2
	>>> shortarray.length # java-style
	2

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
		info, = self.hprof_file.get_class_infos(self.hprof_elem_type.name + '[]')
		return info.class_id

	@property
	def _hprof_len(self):
		return self._hproff.DATA + self.length * self.hprof_elem_type.size(self.hprof_file.idsize)

	def __str__(self):
		content = ', '.join(repr(item) for item in self)
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

	def hprof_decode(self, encoding=None, errors='strict'):
		'''decode a char array into a string; raises TypeError for other array types.

		See python's `codecs` module docs for details on possible encodings and error handlers.

		Params:
		encoding -- the character encoding to use; None will auto-pick based on the array type
		errors -- decoding error handling scheme
		'''
		etype = self.hprof_elem_type
		if etype not in (JavaType.char, JavaType.byte):
			raise TypeError('not a char or byte array', self)

		if encoding is None:
			encoding = 'utf-16-be' if etype == JavaType.char else 'utf-8'
		nbytes = self.length * (2 if etype == JavaType.char else 1)

		start = self.hprof_addr + self._hproff.DATA
		data = self.hprof_file.read_bytes(start, nbytes)
		return data.decode(encoding, errors)

class ObjectArray(Array):
	'''An array of object references.

	The array can be accessed like a normal python array: `len(arr)`, `arr[ix]`, and `for v in arr`
	works as expected.

	null values will be returned as python None values.

	>>> vehicles # doctest: +ELLIPSIS
	ObjectArray(class=java.lang.Object[], id=0x..., length=5)
	>>> print(vehicles) # doctest: +ELLIPSIS
	Object[5] {Car(id=0x...), Car...}
	>>> for v in vehicles:
	...     print(v.make)
	Lolvo
	Yotoya
	Fånark
	Stretch
	Descent
	>>> vehicles[3] # doctest: +ELLIPSIS
	Object(class=com.example.cars.Limo, id=0x...)
	>>> len(vehicles)   # python-style
	5
	>>> vehicles.length # java-style
	5

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
		cid = self.hprof_class_id
		cname = self.hprof_file.get_class_info(cid).class_name
		cname = cname.rsplit('.', 1)[-1]
		try:
			content = ', '.join(str(item) for item in self)
		except Exception:
			content = ', '.join('id=0x%x' % self._hprof_item_id(i) for i in range(self.length))
		left, right = cname.split('[]', 1)
		return '%s[%d]%s {%s}' % (left, self.length, right, content)

	def __repr__(self):
		cid = self.hprof_class_id
		cname = self.hprof_file.get_class_info(cid).class_name
		return 'ObjectArray(class=%s, id=0x%x, length=%d)' % (cname, self.hprof_id, self.length)

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
