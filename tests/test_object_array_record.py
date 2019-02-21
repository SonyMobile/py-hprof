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
			with dump.subrecord(34) as array:
				self.aid = array.id(self.idsize * 31)
				array.uint(1234) # stack trace
				array.uint(5)    # element count
				array.id(112)    # array class id
				self.id1 = array.id(489)
				array.id(self.id1)
				self.id2 = array.id(0x1234567891234567)
				array.id(self.id1)
				array.id(self.id2)
		addrs, data = hb.build()
		self.hf = hprof.open(bytes(data))
		dump, = self.hf.records()
		self.a, = dump.records()

	def tearDown(self):
		self.a = None
		self.hf.close()
		self.hf = None

	### type-specific fields ###

	def test_object_array_stacktrace(self): # TODO
		pass

	def test_object_array_count(self):
		self.assertEqual(self.a.length, 5)

	def test_object_array_values(self):
		self.assertEqual(self.a[0], self.id1)
		self.assertEqual(self.a[1], self.id1)
		self.assertEqual(self.a[2], self.id2)
		self.assertEqual(self.a[3], self.id1)
		self.assertEqual(self.a[4], self.id2)

	def test_object_array_read_outside(self):
		with self.assertRaisesRegex(IndexError, '-1.*5'):
			self.a[-1]
		with self.assertRaisesRegex(IndexError, '5.*5'):
			self.a[5]

	### generic record fields ###

	def test_object_array_addr(self):
		self.assertEqual(self.a.addr, 40)

	def test_object_array_id(self):
		self.assertEqual(self.a.id, self.aid)

	def test_object_array_type(self):
		self.assertIs(type(self.a), hprof.heaprecord.ObjectArrayRecord)

	def test_object_array_tag(self):
		self.assertEqual(self.a.tag, 0x22)

	def test_object_array_len(self):
		self.assertEqual(len(self.a), 1 + 8 + self.idsize * 7)

	def test_object_array_str(self):
		self.assertEqual(str(self.a), 'ObjectArrayRecord(count=5)')
