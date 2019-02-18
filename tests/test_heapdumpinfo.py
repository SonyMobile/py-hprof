#!/usr/bin/env python3
#coding=utf8

from unittest import TestCase

import hprof

from .util import HprofBuilder, varying_idsize


@varying_idsize
class TestHeapDumpInfo(TestCase):
	def setUp(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 12345)
		with hb.record(1, 1) as name:
			self.heapnameid = name.id(167812)
			name.bytes('heap')
		with hb.record(1, 2) as name:
			self.mountainid = name.id(861982141)
			name.bytes('mountain')
		with hb.record(28, 3) as dump:
			with dump.subrecord(0xfe) as info:
				info.uint(77)
				info.id(self.heapnameid)
			with dump.subrecord(0xfe) as info:
				info.uint(18671)
				info.id(self.mountainid)
			with dump.subrecord(0xfe) as info:
				info.uint(77)
				info.id(self.heapnameid)
		self.addrs, self.data = hb.build()
		hf = hprof.open(bytes(self.data))
		_, _, dump = hf.records()
		self.infoA, self.infoB, self.infoC = dump.records()

	def test_heapdumpinfo_class(self):
		self.assertIs(type(self.infoA), hprof.heaprecord.HeapDumpInfo)
		self.assertIs(type(self.infoB), hprof.heaprecord.HeapDumpInfo)
		self.assertIs(type(self.infoC), hprof.heaprecord.HeapDumpInfo)

	def test_heapdumpinfo_name(self):
		self.assertEqual(self.infoA.name.str, 'heap')
		self.assertEqual(self.infoB.name.str, 'mountain')
		self.assertEqual(self.infoC.name.str, 'heap')

	def test_heapdumpinfo_type(self):
		self.assertEqual(self.infoA.type, 77)
		self.assertEqual(self.infoB.type, 18671)
		self.assertEqual(self.infoC.type, 77)

	# TODO: enable this test after refactoring Record class hierarchy
	'''
		def test_heapdumpinfo_equality(self):
			other = hprof.heaprecord.HeapDumpInfo(self.infoA.hf, self.infoA.addr)
			self.assertEqual(self.infoA, other)
			self.assertEqual(self.infoA, self.infoC)
			self.assertEqual(self.infoC, other)
			self.assertEqual(self.infoC, self.infoA)
			self.assertNotEqual(self.infoA, self.infoB)
			self.assertNotEqual(self.infoC, self.infoB)
			self.assertNotEqual(self.infoB, self.infoA)
			self.assertNotEqual(self.infoB, self.infoC)
			self.assertNotEqual(undef, self.infoA)
			self.assertNotEqual(undef, self.infoB)
			self.assertNotEqual(undef, self.infoC)
			self.assertNotEqual(self.infoA, undef)
			self.assertNotEqual(self.infoB, undef)
			self.assertNotEqual(self.infoC, undef)
	'''

	def test_heapdumpinfo_str(self):
		self.assertEqual(str(self.infoA), 'HeapDumpInfo(type=77 name=heap)')
		self.assertEqual(str(self.infoB), 'HeapDumpInfo(type=18671 name=mountain)')
		self.assertEqual(str(self.infoC), 'HeapDumpInfo(type=77 name=heap)')
