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
				id2 = root.id(0x998877341)
			with dump.subrecord(33) as obj:
				id1 = obj.id(0x198877341)
				obj.uint(0x1789)
				obj.id(0x12345)
				obj.uint(4)
				obj.uint(0x1badd00d)
			with dump.subrecord(33) as obj:
				obj.id(id2)
				obj.uint(0x1779)
				obj.id(0x12345)
				obj.uint(10)
				obj.uint(0x2badd00d)
				obj.ushort(0x1020)
				obj.uint(0x1)
			with dump.subrecord(8) as root:
				root.id(id1)
				root.uint(500)
				root.uint(555)
			with dump.subrecord(2) as root:
				root.id(id1)
				root.uint(78)
				root.uint(0xffffffff)
			with dump.subrecord(2) as root:
				root.id(id2)
				root.uint(78)
				root.uint(2)
		self.addrs, self.data = hb.build()
		hf = hprof.open(bytes(self.data))
		dump = next(hf.records())
		(
			self.unknownroot, self.obj1, self.obj2, self.threadroot,
			self.localjniroot1, self.localjniroot2,
		) = dump.records()

	### type-specific fields ###

	def test_root_obj_types(self):
		self.assertIs(type(self.obj1), hprof.heaprecord.Object)
		self.assertIs(type(self.obj2), hprof.heaprecord.Object)

	def test_root_obj(self):
		self.assertEqual(self.unknownroot       .obj, self.obj2)
		self.assertEqual(self.threadroot        .obj, self.obj1)
		self.assertEqual(self.localjniroot1     .obj, self.obj1)
		self.assertEqual(self.localjniroot2     .obj, self.obj2)

	def test_threadroot_thread(self):
		pass # TODO: we don't know about threads yet

	def test_threadroot_stacktrace(self):
		pass # TODO: we don't know about stack traces yet

	def test_localjniroot_stacktrace(self):
		pass # TODO: we don't know about stack traces yet

	### generic record fields ###

	def test_root_id(self):
		with self.assertRaisesRegex(AttributeError, r'\bid\b'):
			self.unknownroot.id
		with self.assertRaisesRegex(AttributeError, r'\bid\b'):
			self.threadroot.id
		with self.assertRaisesRegex(AttributeError, r'\bid\b'):
			self.localjniroot1.id
		with self.assertRaisesRegex(AttributeError, r'\bid\b'):
			self.localjniroot2.id

	def test_root_type(self):
		self.assertIs(type(self.unknownroot),      hprof.heaprecord.UnknownRoot)
		self.assertIs(type(self.threadroot),       hprof.heaprecord.ThreadRoot)
		self.assertIs(type(self.localjniroot1),    hprof.heaprecord.LocalJniRoot)
		self.assertIs(type(self.localjniroot2),    hprof.heaprecord.LocalJniRoot)

	def test_root_tag(self):
		self.assertEqual(self.unknownroot       .tag, 0xff)
		self.assertEqual(self.threadroot        .tag, 0x08)
		self.assertEqual(self.localjniroot1     .tag, 0x02)
		self.assertEqual(self.localjniroot2     .tag, 0x02)

	def test_root_len(self):
		self.assertEqual(len(self.unknownroot),        1 + self.idsize)
		self.assertEqual(len(self.threadroot),         9 + self.idsize)
		self.assertEqual(len(self.localjniroot1),      9 + self.idsize)
		self.assertEqual(len(self.localjniroot2),      9 + self.idsize)

	def test_root_str(self):
		# TODO: when we know about threads and classes, improve expected str() result.
		self.assertEqual(str(self.unknownroot),        'UnknownRoot(Object(class=TODO))')
		self.assertEqual(str(self.threadroot),         'ThreadRoot(Object(class=TODO) from thread ???)')
		self.assertEqual(str(self.localjniroot1),      'LocalJniRoot(Object(class=TODO) in <func>)')
		self.assertEqual(str(self.localjniroot2),      'LocalJniRoot(Object(class=TODO) in <func>)')
