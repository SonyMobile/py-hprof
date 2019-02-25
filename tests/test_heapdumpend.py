#!/usr/bin/env python3
#coding=utf8

from datetime import datetime, timedelta
from struct import pack
from unittest import TestCase

import hprof

from .util import HprofBuilder, varying_idsize

@varying_idsize
class TestHeapDumpEnd(TestCase):
	def setUp(self):
		builder = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 0x0168e143f263)
		with builder.record(44, 7020) as r:
			pass
		self.addrs, self.data = builder.build()
		self.f = hprof.open(bytes(self.data))
		self.e = list(self.f.records())[0]

	def tearDown(self):
		self.e = None
		self.f.close()
		self.f = None

	### generic record fields ###

	def test_heapdumpend_addr(self):
		self.assertEqual(self.e.hprof_addr, self.addrs[0])

	def test_heapdumpend_type(self):
		self.assertIs(type(self.e), hprof.record.HeapDumpEnd)

	def test_heapdumpend_rawbody(self):
		self.assertEqual(self.e.rawbody, b'')

	def test_heapdumpend_len(self):
		self.assertEqual(self.e._hprof_len, 9)

	def test_heapdumpend_str(self):
		self.assertEqual(str(self.e), 'HeapDumpEnd()')

@varying_idsize
class TestHeapDumpErrors(TestCase):
	def test_heapdumpend_with_data(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 0x0168e143f263)
		with hb.record(44, 123) as r:
			r.uint(7878)
		addrs, data = hb.build()
		hf = hprof.open(bytes(data))
		end, = hf.records()
		self.assertEqual(end._hprof_len, 13)

