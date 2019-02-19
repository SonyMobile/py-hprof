#!/usr/bin/env python3
#coding=utf8

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
		self.assertEqual(self.a.count, self.COUNT)

	def test_primitive_array_type(self):
		self.assertEqual(self.a.type.value, self.ETYPE)
		self.assertEqual(self.a.type.name, self.ENAME)

	def test_primitive_array_values(self):
		for i in range(self.COUNT):
			self.assertEqual(self.a[i], self._val(i))

	def test_primitive_array_read_outside(self):
		with self.assertRaisesRegex(IndexError, '-1.*%s' % self.COUNT):
			self.a[-1]
		with self.assertRaisesRegex(IndexError, '%s.*%s' % (self.COUNT, self.COUNT)):
			self.a[self.COUNT]

	### generic record fields ###

	def test_primitive_array_addr(self):
		self.assertEqual(self.a.addr, 40)

	def test_primitive_array_id(self):
		self.assertEqual(self.a.id, self.aid)

	def test_primitive_array_type(self):
		self.assertIs(type(self.a), hprof.heaprecord.PrimitiveArrayRecord)

	def test_primitive_array_tag(self):
		self.assertEqual(self.a.tag, 0x23)

	def test_primitive_array_len(self):
		self.assertEqual(len(self.a), 10 + self.idsize + self.COUNT * self.ESIZE)

	def test_primitive_array_str(self):
		self.assertEqual(str(self.a), 'PrimitiveArrayRecord(type=%s, count=%d)' % (self.ENAME, self.COUNT))


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
		return (i * 16) % 256
	def _add(self, array, i):
		array.byte(self._val(i))

class TestCharArrayRecord(TestPrimitiveArrayRecord):
	COUNT = 33
	ETYPE = 5
	ESIZE = 2
	ENAME = 'char'
	def _val(self, i):
		if i == 0:
			return '学'
		elif i == 1:
			return 'Ꚛ'
		else:
			return chr(65 + i)
	def _add(self, array, i):
		if i == 0:
			array.ushort(0x5b66)
		elif i == 1:
			array.ushort(0xa69a)
		else:
			array.ushort(65 + i)

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
