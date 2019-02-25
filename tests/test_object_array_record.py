#!/usr/bin/env python3
#coding=utf8

from struct import pack, unpack
from unittest import TestCase

from .util import HprofBuilder, varying_idsize

import hprof

@varying_idsize
class TestObjArrayRecord(TestCase):
	def setUp(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 787878)
		with hb.record(28, 0) as dump:
			with dump.subrecord(33) as obj1:
				self.id1 = obj1.id(489)
				obj1.uint(0)
				obj1.id(1010)
				obj1.uint(0)
			with dump.subrecord(34) as array:
				self.aid = array.id(self.idsize * 31)
				array.uint(1234) # stack trace
				array.uint(5)    # element count
				array.id(112)    # array class id
				array.id(self.id1)
				array.id(self.id1)
				self.id2 = array.id(0x1234567891234567)
				array.id(self.id1)
				array.id(self.id2)
			with dump.subrecord(33) as obj2:
				obj2.id(self.id2)
				obj2.uint(0)
				obj2.id(1010)
				obj2.uint(0)
		addrs, data = hb.build()
		self.hf = hprof.open(bytes(data))
		dump, = self.hf.dumps()
		heap, = dump.heaps()
		self.obj1, self.a, self.obj2 = sorted(heap.objects(), key=lambda r: r.hprof_addr)

	def tearDown(self):
		self.a = None
		self.hf.close()
		self.hf = None

	### type-specific fields ###

	def test_object_array_stacktrace(self): # TODO
		pass

	def test_object_array_count(self):
		self.assertEqual(self.a.length, 5)
		self.assertEqual(len(self.a), 5)

	def test_object_array_values(self):
		self.assertEqual(self.a[0].hprof_id, self.id1)
		self.assertEqual(self.a[1].hprof_id, self.id1)
		self.assertEqual(self.a[2].hprof_id, self.id2)
		self.assertEqual(self.a[3].hprof_id, self.id1)
		self.assertEqual(self.a[4].hprof_id, self.id2)
		self.assertEqual(self.a[0], self.obj1)
		self.assertEqual(self.a[1], self.obj1)
		self.assertEqual(self.a[2], self.obj2)
		self.assertEqual(self.a[3], self.obj1)
		self.assertEqual(self.a[4], self.obj2)

	def test_object_array_iterable(self):
		iterator = iter(self.a)
		self.assertEqual(next(iterator), self.obj1)
		self.assertEqual(next(iterator), self.obj1)
		self.assertEqual(next(iterator), self.obj2)
		self.assertEqual(next(iterator), self.obj1)
		self.assertEqual(next(iterator), self.obj2)
		with self.assertRaises(StopIteration):
			next(iterator)

	def test_object_array_loopable(self):
		expected = (self.obj1, self.obj1, self.obj2, self.obj1, self.obj2)
		for i, o in enumerate(self.a):
			self.assertEqual(o, expected[i])

	def test_object_array_to_tuple(self):
		self.assertEqual(tuple(self.a), (self.obj1, self.obj1, self.obj2, self.obj1, self.obj2))

	def test_object_array_read_outside(self):
		with self.assertRaisesRegex(IndexError, '-1.*5'):
			self.a[-1]
		with self.assertRaisesRegex(IndexError, '5.*5'):
			self.a[5]

	### generic record fields ###

	def test_object_array_addr(self):
		self.assertEqual(self.a.hprof_addr, 49 + self.idsize * 2)

	def test_object_array_id(self):
		self.assertEqual(self.a.hprof_id, self.aid)

	def test_object_array_type(self):
		self.assertIs(type(self.a), hprof.heap.ObjectArray)

	def test_object_array_len(self):
		self.assertEqual(self.a._hprof_len, 1 + 8 + self.idsize * 7)

	def test_object_array_str(self):
		self.assertEqual(str(self.a), 'ObjectArray(id=0x%x, count=5)' % self.aid)
