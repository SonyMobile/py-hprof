from unittest import TestCase

from .util import HprofBuilder

import hprof

class TestJavaStringValue(TestCase):
	def setUp(self):
		self.idsize = 7
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 10102030)
		hb.name(1, 'java.lang.Object')
		hb.name(2, 'java.lang.String')
		hb.name(3, 'char[]')
		hb.name(4, 'byte[]')
		hb.name(5, 'java.lang.Class')
		self.add_records(hb)
		with hb.record(2, 0) as load: # java.lang.Object
			load.uint(11)
			load.id(21) # class obj
			load.uint(0)
			load.id(1)  # name
		with hb.record(2, 0) as load: # java.lang.String
			load.uint(12)
			load.id(22) # class obj
			load.uint(0)
			load.id(2)  # name
		with hb.record(2, 0) as load: # char[]
			load.uint(13)
			load.id(23) # class obj
			load.uint(0)
			load.id(3)  # name
		with hb.record(2, 0) as load: # byte[]
			load.uint(14)
			load.id(24) # class obj
			load.uint(0)
			load.id(4)  # name
		with hb.record(2, 0) as load: # java.lang.Class
			load.uint(15)
			load.id(25)
			load.uint(0)
			load.id(5)
		with hb.record(28, 0) as dump:
			with dump.subrecord(32) as cls:
				cls.id(21)
				cls.uint(0)
				cls.id(0)
				cls.id(0)
				cls.id(0)
				cls.id(0)
				cls.id(0)
				cls.id(0)
				cls.uint(8)
				cls.ushort(0)
				cls.ushort(0)
				cls.ushort(0)
			with dump.subrecord(32) as cls:
				cls.id(22)
				cls.uint(0)
				cls.id(21)
				cls.id(0)
				cls.id(0)
				cls.id(0)
				cls.id(0)
				cls.id(0)
				cls.uint(16)
				cls.ushort(0)
				cls.ushort(0)
				self.add_instance_fields(cls)
			with dump.subrecord(33) as obj:
				obj.id(32)
				obj.uint(0)
				obj.id(22)
				self.add_string_data1(obj)
			with dump.subrecord(33) as obj:
				obj.id(33)
				obj.uint(0)
				obj.id(22)
				self.add_string_data2(obj)
			self.add_heap_records(dump)
		addrs, data = hb.build()
		hf = hprof.open(bytes(data))
		dump, = hf.dumps()
		self.string1, self.string2 = dump.find_instances('java.lang.String')

	def add_records(self, hb):
		hb.name(9, 'value')
		hb.name(8, 'hash')

	def add_instance_fields(self, cls):
		cls.ushort(2)
		cls.id(9) # name ('value')
		cls.byte(2) # type (object)
		cls.id(8) # name ('hash')
		cls.byte(10) # type (int)

	def add_string_data1(self, obj):
		obj.uint(self.idsize + 4)
		obj.id(37)
		obj.uint(999)

	def add_string_data2(self, obj):
		obj.uint(self.idsize + 4)
		obj.id(36)
		obj.uint(998)

	def add_heap_records(self, dump):
		s = 'ABC 𣲷 ÅÄÖ \0\1\2 学 åäö'
		b = s.encode('utf-16-be')
		if len(b) & 1:
			raise Exception('odd byte count')
		nelems = len(b) >> 1
		with dump.subrecord(35) as data:
			data.id(37)
			data.uint(0)
			data.uint(nelems)
			data.byte(5) # element type (char)
			data.bytes(b)
		with dump.subrecord(35) as data:
			data.id(36)
			data.uint(0)
			data.uint(nelems)
			data.byte(5) # element type (char)
			data.bytes(b)

	def test_string_object_str(self):
		self.assertEqual(str(self.string1), 'ABC 𣲷 ÅÄÖ \0\1\2 学 åäö')

	def test_string_object_repr(self):
		self.assertEqual(repr(self.string1), 'Object(class=java.lang.String, id=0x20, value=%r)' % 'ABC 𣲷 ÅÄÖ \0\1\2 学 åäö')

	def test_string_object_eq(self):
		created = hprof.heap.Object(self.string1.hprof_file, self.string1.hprof_addr)
		self.assertEqual(self.string1, self.string1)
		self.assertEqual(self.string1, created)
		self.assertEqual(created, self.string1)
		self.assertEqual(self.string1, 'ABC 𣲷 ÅÄÖ \0\1\2 学 åäö')
		self.assertEqual('ABC 𣲷 ÅÄÖ \0\1\2 学 åäö', self.string1)
		self.assertEqual(self.string1, self.string2)
		self.assertEqual(self.string2, self.string1)
		with self.assertRaisesRegex(AttributeError, 'no hprof_heap'):
			self.assertEqual(self.string2, created)
		with self.assertRaisesRegex(AttributeError, 'no hprof_heap'):
			self.assertEqual(created, self.string2)

class TestAndroidCompressedStringValue(TestJavaStringValue):
	def add_records(self, hb):
		hb.name(9, 'count')
		hb.name(8, 'value')

	def add_instance_fields(self, cls):
		cls.ushort(2)
		cls.id(9) # name ('count')
		cls.byte(10) # type (int)
		cls.id(8) # name ('value')
		cls.byte(2) # type (object)

	def add_string_data1(self, obj):
		obj.uint(self.idsize + 4)
		obj.uint(20)
		obj.id(38)

	def add_string_data2(self, obj):
		obj.uint(self.idsize + 4)
		obj.uint(20)
		obj.id(37)

	def add_heap_records(self, dump):
		# technically, ART only compresses all-ascii strings to bytes, but let's be generous
		# and support utf-8.
		s = 'ABC 𣲷 ÅÄÖ \0\1\2 学 åäö'
		b = s.encode('utf-8')
		with dump.subrecord(35) as data:
			data.id(38)
			data.uint(0)
			data.uint(len(b)) # elem count
			data.byte(8) # element type (byte)
			data.bytes(b)
		with dump.subrecord(35) as data:
			data.id(37)
			data.uint(0)
			data.uint(len(b)) # elem count
			data.byte(8) # element type (byte)
			data.bytes(b)

class TestBadStringValue(TestJavaStringValue):
	def add_records(self, hb):
		hb.name(7, 'value')

	def add_instance_fields(self, cls):
		cls.ushort(1)
		cls.id(7) # name ('value')
		cls.byte(2) # type (object)

	def add_string_data1(self, obj):
		obj.uint(self.idsize)
		obj.id(0) # a null!

	def add_string_data2(self, obj):
		obj.uint(self.idsize)
		obj.id(33) # itself!

	def add_heap_records(self, dump):
		pass

	def test_string_object_str(self):
		self.assertEqual(str(self.string1), '')
		self.assertEqual(str(self.string2), 'String(id=0x21)')

	def test_string_object_repr(self):
		self.assertEqual(repr(self.string1), 'Object(class=java.lang.String, id=0x20, value=\'\')')
		self.assertEqual(repr(self.string2), 'Object(class=java.lang.String, id=0x21)')

	def test_string_object_eq(self):
		created = hprof.heap.Object(self.string1.hprof_file, self.string1.hprof_addr)
		self.assertEqual(self.string1, self.string1)
		self.assertEqual(self.string1, created)
		self.assertEqual(created, self.string1)
		self.assertEqual(self.string1, '')
		self.assertEqual('', self.string1)

		with self.assertRaisesRegex(hprof.UnfamiliarStringError, 'decode'):
			self.string2 == 'ABC 𣲷 ÅÄÖ \0\1\2 学 åäö'
		with self.assertRaisesRegex(hprof.UnfamiliarStringError, 'decode'):
			'ABC 𣲷 ÅÄÖ \0\1\2 学 åäö' == self.string2

		with self.assertRaises(hprof.UnfamiliarStringError):
			self.string1 == self.string2
		with self.assertRaises(hprof.UnfamiliarStringError):
			self.string2 == self.string1
		with self.assertRaises((AttributeError, hprof.UnfamiliarStringError)):
			self.string2 == created
		with self.assertRaises((AttributeError, hprof.UnfamiliarStringError)):
			created == self.string2
		with self.assertRaisesRegex(AttributeError, 'hprof_heap'):
			created == 'abcd'
		with self.assertRaisesRegex(AttributeError, 'hprof_heap'):
			'abcd' == created

class TestMissingStringValue(TestJavaStringValue):
	def add_records(self, hb):
		pass # nothing to add

	def add_instance_fields(self, cls):
		cls.ushort(0) # no instance fields!

	def add_string_data1(self, obj):
		obj.uint(0) # no field bytes.

	def add_string_data2(self, obj):
		obj.uint(0) # no field bytes.

	def add_heap_records(self, dump):
		pass

	def test_string_object_str(self):
		self.assertEqual(str(self.string1), 'String(id=0x20)')
		self.assertEqual(str(self.string2), 'String(id=0x21)')

	def test_string_object_repr(self):
		self.assertEqual(repr(self.string1), 'Object(class=java.lang.String, id=0x20)')
		self.assertEqual(repr(self.string2), 'Object(class=java.lang.String, id=0x21)')

	def test_string_object_eq(self):
		created = hprof.heap.Object(self.string1.hprof_file, self.string1.hprof_addr)
		self.assertEqual(self.string1, self.string1)
		self.assertEqual(self.string1, created)
		self.assertEqual(created, self.string1)

		with self.assertRaisesRegex(hprof.UnfamiliarStringError, 'unfamiliar'):
			self.string1 == 'ABC 𣲷 ÅÄÖ \0\1\2 学 åäö'
		with self.assertRaisesRegex(hprof.UnfamiliarStringError, 'unfamiliar'):
			'ABC 𣲷 ÅÄÖ \0\1\2 学 åäö' == self.string1

		with self.assertRaisesRegex(hprof.UnfamiliarStringError, 'unfamiliar'):
			self.string2 == 'ABC 𣲷 ÅÄÖ \0\1\2 学 åäö'
		with self.assertRaisesRegex(hprof.UnfamiliarStringError, 'unfamiliar'):
			'ABC 𣲷 ÅÄÖ \0\1\2 学 åäö' == self.string2

		with self.assertRaises(hprof.UnfamiliarStringError):
			self.string1 == self.string2
		with self.assertRaises(hprof.UnfamiliarStringError):
			self.string2 == self.string1
		with self.assertRaises((AttributeError, hprof.UnfamiliarStringError)):
			self.string2 == created
		with self.assertRaises((AttributeError, hprof.UnfamiliarStringError)):
			created == self.string2
