# Copyright (C) 2019 Sony Mobile Communications Inc.
# Licensed under the LICENSE

from struct import pack, unpack
from unittest import TestCase

from .util import HprofBuilder, varying_idsize

import hprof

class TestPrimitiveArrayRecord(TestCase):
	idsize = 5
	COUNT = 7
	ETYPE = 10
	ESIZE = 4
	ENAME = 'int'

	def setUp(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 1234567)
		with hb.record(28, 0) as dump:
			with dump.subrecord(35) as array:
				self.aid = array.id(self.COUNT * self.ETYPE * 31)
				array.uint(1234) # stack trace
				array.uint(self.COUNT) # element count
				array.byte(self.ETYPE) # element type
				for i in range(self.COUNT):
					self._add(array, i)
		addrs, data = hb.build()
		self.hf = hprof.open(bytes(data))
		dump, = self.hf.records()
		self.a, = dump.records()

	def tearDown(self):
		self.hf.close()

	def _val(self, i):
		return 101 * i - 500

	def _add(self, array, i):
		array.int(self._val(i))

	### type-specific fields ###

	def test_primitive_array_stacktrace(self): # TODO
		pass

	def test_primitive_array_count(self):
		self.assertEqual(self.a.length, self.COUNT)
		self.assertEqual(len(self.a), self.COUNT)

	def test_primitive_array_type(self):
		self.assertEqual(self.a.type.value, self.ETYPE)
		self.assertEqual(self.a.type.name, self.ENAME)

	def test_primitive_array_values(self):
		for i in range(self.COUNT):
			self.assertEqual(self.a[i], self._val(i))

	def test_primitive_array_iterable(self):
		iterator = iter(self.a)
		for i in range(self.COUNT):
			self.assertEqual(next(iterator), self._val(i))
		with self.assertRaises(StopIteration):
			next(iterator)

	def test_primitive_array_loopable(self):
		for i, o in enumerate(self.a):
			self.assertEqual(o, self._val(i))

	def test_primitive_array_to_tuple(self):
		self.assertEqual(tuple(self.a), tuple(self._val(i) for i in range(self.COUNT)))

	def test_primitive_array_read_outside(self):
		with self.assertRaisesRegex(IndexError, '-1.*%s' % self.COUNT):
			self.a[-1]
		with self.assertRaisesRegex(IndexError, '%s.*%s' % (self.COUNT, self.COUNT)):
			self.a[self.COUNT]

	### generic record fields ###

	def test_primitive_array_addr(self):
		self.assertEqual(self.a.hprof_addr, 40)

	def test_primitive_array_id(self):
		self.assertEqual(self.a.hprof_id, self.aid)

	def test_primitive_array_type(self):
		self.assertIs(type(self.a), hprof.heap.PrimitiveArray)

	def test_primitive_array_len(self):
		self.assertEqual(self.a._hprof_len, 10 + self.idsize + self.COUNT * self.ESIZE)

	def test_primitive_array_str(self):
		values = ', '.join(repr(self._val(i)) for i in range(self.COUNT))
		self.assertEqual(str(self.a), '%s[%d] {%s}' % (self.ENAME, self.COUNT, values))

	def test_primitive_array_repr(self):
		self.assertEqual(repr(self.a), 'PrimitiveArray(type=%s, id=0x%x, length=%d)' % (self.ENAME, self.aid, self.COUNT))

	def test_primitive_array_str_encodeable(self):
		try:
			str(self.a).encode('utf-8')
		except Exception as e:
			self.fail(e)

	def test_primitive_array_repr_encodeable(self):
		try:
			repr(self.a).encode('utf-8')
		except Exception as e:
			self.fail(e)

class TestBooleanArrayRecord(TestPrimitiveArrayRecord):
	COUNT = 790
	ETYPE = 4
	ESIZE = 1
	ENAME = 'boolean'
	def _val(self, i):
		return (i * i) % 7 != 0
	def _add(self, array, i):
		array.byte(int(self._val(i)))

class TestByteArrayRecord(TestPrimitiveArrayRecord):
	COUNT = 33
	ETYPE = 8
	ESIZE = 1
	ENAME = 'byte'

	def _val(self, i):
		if i == 10:
			return 0xf0
		elif i == 11:
			return 0xa3
		elif i == 12:
			return 0xb2
		elif i == 13:
			return 0xb7
		return 80 + i

	def _add(self, array, i):
		array.byte(self._val(i))

	def test_byte_array_decode(self):
		self.assertEqual(self.a.hprof_decode(), 'PQRSTUVWXY𣲷^_`abcdefghijklmnop')

	def test_byte_array_str(self):
		self.assertEqual(str(self.a), 'byte[33] {80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 240, 163, 178, 183, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112}')

	def test_byte_array_repr(self):
		self.assertEqual(repr(self.a), 'PrimitiveArray(type=byte, id=0x%x, length=33)' % self.aid)

class TestCharArrayRecord(TestPrimitiveArrayRecord):
	COUNT = 33
	ETYPE = 5
	ESIZE = 2
	ENAME = 'char'
	def _val(self, i):
		if i == 3:
			return '学'
		elif i == 10:
			return '\ud84f'
		elif i == 11:
			return '\udcb7'
		else:
			return chr(65 + i)
	def _add(self, array, i):
		if i == 3:
			array.ushort(0x5b66)
		elif i == 10:
			array.bytes('𣲷'.encode('utf-16-be'))
		elif i == 11:
			pass # 𣲷 takes two Java chars; add nothing (note how both K an L are gone below)
		else:
			array.ushort(65 + i)

	def test_char_array_decode(self):
		self.assertEqual(self.a.hprof_decode(), 'ABC学EFGHIJ𣲷MNOPQRSTUVWXYZ[\\]^_`a')

	def test_char_array_str(self):
		self.assertEqual(str(self.a), '''char[33] {'A', 'B', 'C', '学', 'E', 'F', 'G', 'H', 'I', 'J', '\\ud84f', '\\udcb7', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', '\\\\', ']', '^', '_', '`', 'a'}''')

	def test_char_array_repr(self):
		self.assertEqual(repr(self.a), 'PrimitiveArray(type=char, id=0x%x, length=33)' % self.aid)

class TestShortArrayRecord(TestPrimitiveArrayRecord):
	idsize = 4
	COUNT = 13
	ETYPE = 9
	ESIZE = 2
	ENAME = 'short'
	def _val(self, i):
		return 13 + 3 * i - 20
	def _add(self, array, i):
		array.short(self._val(i))

class TestLongArrayReceord(TestPrimitiveArrayRecord):
	idsize = 2
	COUNT = 11
	ETYPE = 11
	ESIZE = 8
	ENAME = 'long'
	def _val(self, i):
		return (i - 5) * 10000000000
	def _add(self, array, i):
		array.long(self._val(i))

class TestFloatArrayRecord(TestPrimitiveArrayRecord):
	idsize = 7
	COUNT = 5
	ETYPE = 6
	ESIZE = 4
	ENAME = 'float'
	def _val(self, i):
		if i > 2:
			f = float(1000.0 / i)
		else:
			f = float(-7.0 * i)
		f, = unpack('f', pack('f', f))
		return f
	def _add(self, array, i):
		array.float(self._val(i))

	def test_float_array_decode(self):
		with self.assertRaisesRegex(TypeError, 'char or byte array'):
			self.a.hprof_decode()

class TestDoubleArrayRecord(TestPrimitiveArrayRecord):
	COUNT = 9
	ETYPE = 7
	ESIZE = 8
	ENAME = 'double'
	def _val(self, i):
		if i & 3:
			return -i * 1.33
		else:
			return i**1.01
	def _add(self, array, i):
		array.double(self._val(i))

class TestPrimitiveArrayTypeErrors(TestCase):
	def test_bad_elem_type(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', 4, 1234567)
		with hb.record(28, 0) as dump:
			with dump.subrecord(35) as array:
				aid = array.id(4000)
				array.uint(1234) # stack trace
				array.uint(13) # element count
				array.byte(50) # element type
				for i in range(13):
					array.byte(17)
		addrs, data = hb.build()
		hf = hprof.open(bytes(data))
		dump, = hf.records()
		with self.assertRaisesRegex(hprof.FileFormatError, 'JavaType'):
			arr, = dump.records()

	def test_bad_bool_value(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', 4, 1234567)
		with hb.record(28, 0) as dump:
			with dump.subrecord(35) as array:
				aid = array.id(4000)
				array.uint(1234) # stack trace
				array.uint(13) # element count
				array.byte(4) # element type
				for i in range(12):
					array.byte(i+2)
				array.byte(255)
		addrs, data = hb.build()
		hf = hprof.open(bytes(data))
		dump, = hf.records()
		arr, = dump.records()
		with self.assertRaisesRegex(hprof.FileFormatError, 'invalid boolean value 0xff'):
			arr[12]
		for i in range(12):
			with self.assertRaisesRegex(hprof.FileFormatError, 'invalid boolean value 0x%x' % (i+2)):
				arr[i]
