#!/usr/bin/env python3
#coding=utf8

from unittest import TestCase

from .util import HprofBuilder, varying_idsize

import hprof

@varying_idsize
class TestRoots(TestCase):
	def setUp(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 1234567890)
		with hb.record(28, 0) as dump:
			with dump.subrecord(255) as root:
				id1 = root.id(0x998877341)
			with dump.subrecord(33) as obj:
				id2 = obj.id(0x198877341)
				obj.uint(0x1789)
				obj.id(0x12345)
				obj.uint(4)
				obj.uint(0x1badd00d)
			with dump.subrecord(33) as obj:
				obj.id(id1)
				obj.uint(0x1779)
				obj.id(0x12345)
				obj.uint(10)
				obj.uint(0x2badd00d)
				obj.ushort(0x1020)
				obj.uint(0x1)
			with dump.subrecord(8) as root:
				root.id(id2)
				root.uint(500)
				root.uint(555)
		self.addrs, self.data = hb.build()
		hf = hprof.open(bytes(self.data))
		dump = next(hf.records())
		self.unknownroot, self.obj1, self.obj2, self.threadroot = dump.records()

	### type-specific fields ###

	def test_root_obj(self):
		self.assertIs(type(self.unknownroot       .obj), hprof.heaprecord.Object)
		self.assertIs(type(self.threadroot        .obj), hprof.heaprecord.Object)
		self.assertEqual(  self.unknownroot       .obj, self.obj2)
		self.assertEqual(  self.threadroot        .obj, self.obj1)

	def test_threadroot_thread(self):
		pass # TODO: we don't know about threads yet

	def test_threadroot_stacktrace(self):
		pass # TODO: we don't know about stack traces yet

	### generic record fields ###

	def test_root_id(self):
		with self.assertRaisesRegex(AttributeError, r'\bid\b'):
			self.unknownroot.id
		with self.assertRaisesRegex(AttributeError, r'\bid\b'):
			self.threadroot.id

	def test_root_type(self):
		self.assertIs(type(self.unknownroot),      hprof.heaprecord.UnknownRoot)
		self.assertIs(type(self.threadroot),       hprof.heaprecord.ThreadRoot)

	def test_root_tag(self):
		self.assertEqual(self.unknownroot       .tag, 0xff)
		self.assertEqual(self.threadroot        .tag, 0x08)

	def test_root_len(self):
		self.assertEqual(len(self.unknownroot),        1 + self.idsize)
		self.assertEqual(len(self.threadroot),         9 + self.idsize)

	def test_root_str(self):
		# TODO: when we know about threads and classes, improve expected str() result.
		self.assertEqual(str(self.unknownroot),        'UnknownRoot(Object(class=TODO))')
		self.assertEqual(str(self.threadroot),         'ThreadRoot(Object(class=TODO) from thread ???)')
