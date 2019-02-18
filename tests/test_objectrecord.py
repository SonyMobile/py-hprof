#!/usr/bin/env python3
#coding=utf8

from unittest import TestCase

from .util import HprofBuilder, varying_idsize

import hprof

@varying_idsize
class TestObject(TestCase):
	def setUp(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 1234567890)
		with hb.record(28, 0) as dump:
			with dump.subrecord(33) as obj:
				self.id1 = obj.id(0x998877341)
				obj.uint(0x1789)
				self.cls1 = obj.id(0x12345)
				obj.uint(4)
				obj.uint(0x1badd00d)
			with dump.subrecord(33) as obj:
				self.id2 = obj.id(0x198877341)
				obj.uint(0x1779)
				self.cls2 = obj.id(0x12345)
				obj.uint(10)
				obj.uint(0x2badd00d)
				obj.ushort(0x1020)
				obj.uint(0x1)
		self.addrs, self.data = hb.build()
		hf = hprof.open(bytes(self.data))
		dump = next(hf.records())
		self.o, self.p = dump.records()

	### type-specific fields ###

	def test_object_stacktrace(self):
		pass # TODO: we don't know about stacktraces yet

	def test_object_class(self):
		pass # TODO: we don't know about classes yet

	def test_object_fields(self):
		pass # TODO: we don't know about classes yet, so we don't know the field names...
		# something like: self.assertEqual(self.o.mValue, 0x1badd00d) etc...

	### generic record fields ###

	def test_object_addr(self):
		self.assertEqual(self.o.addr, self.addrs[0] + 9)
		self.assertEqual(self.p.addr, self.addrs[0] + 9 + 13 + 2 * self.idsize)

	def test_object_id(self):
		self.assertEqual(self.o.id, self.id1)
		self.assertEqual(self.p.id, self.id2)

	def test_object_type(self):
		self.assertIs(type(self.o), hprof.heaprecord.ObjectRecord)
		self.assertIs(type(self.p), hprof.heaprecord.ObjectRecord)

	def test_object_tag(self):
		self.assertEqual(self.o.tag, 33)
		self.assertEqual(self.p.tag, 33)

	def test_object_len(self):
		self.assertEqual(len(self.o), 13 + 2 * self.idsize)
		self.assertEqual(len(self.p), 19 + 2 * self.idsize)

	def test_object_str(self):
		# TODO: when we know about classes, it should be part of the str output
		self.assertEqual(str(self.o), 'ObjectRecord(id=0x%x)' % self.id1)
		self.assertEqual(str(self.p), 'ObjectRecord(id=0x%x)' % self.id2)
