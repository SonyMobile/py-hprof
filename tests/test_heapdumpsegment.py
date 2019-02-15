#!/usr/bin/env python3
#coding=utf8

from datetime import datetime, timedelta
from struct import pack
from unittest import TestCase

import hprof

from .util import HprofBuilder, varying_idsize

@varying_idsize
class TestHeapDumpSegment(TestCase):
	def setUp(self):
		builder = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 0x0168e143f263)
		with builder.record(28, 7019) as r:
			with r.subrecord(0xff) as s:
				s.id(0x123456789)
			with r.subrecord(0xff) as s:
				s.id(0x987654321)
		self.addrs, self.data = builder.build()
		self.f = hprof.open(bytes(self.data))
		self.d = list(self.f.records())[0]

	def tearDown(self):
		self.d = None
		self.f.close()
		self.f = None

	### type-specific fields ###

	def test_heapdumpsegment_subrecords(self):
		subs = self.d.records()
		a = next(subs)
		b = next(subs)
		with self.assertRaises(StopIteration):
			next(subs)
		self.assertEqual(a.addr, self.d.addr + 9)
		self.assertEqual(b.addr, self.d.addr + 9 + len(a))
		self.assertEqual(len(a), 1 + self.idsize)
		self.assertEqual(len(b), 1 + self.idsize)

	### generic record fields ###

	def test_heapdumpsegment_addr(self):
		self.assertEqual(self.d.addr, self.addrs[0])

	def test_heapdumpsegment_id(self):
		with self.assertRaisesRegex(AttributeError, 'has no id'):
			self.d.id

	def test_heapdumpsegment_type(self):
		self.assertIs(type(self.d), hprof.record.HeapDumpSegment)

	def test_heapdumpsegment_tag(self):
		self.assertEqual(self.d.tag, 28)

	def test_heapdumpsegment_rawbody(self):
		self.assertEqual(self.d.rawbody, self.data[self.addrs[0] + 9:])

	def test_heapdumpsegment_len(self):
		self.assertEqual(len(self.d), len(self.data) - self.addrs[0])

	def test_heapdumpsegment_str(self):
		self.assertEqual(str(self.d), 'HeapDumpSegment(payloadsize=%d)' % (2 + 2 * self.idsize))

@varying_idsize
class TestHeapDumpSegmentErrors(TestCase):
	def setUp(self):
		self.hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 0x0168e143f263)

	def test_heapdumpsegment_unknown_subtag(self):
		with self.hb.record(28, 123) as r:
			with r.subrecord(0xf0) as s:
				s.bytes('this should not work')
		addrs, data = self.hb.build()
		data = bytes(data)
		with self.assertRaisesRegex(hprof.FileFormatError, '0xf0'):
			hprof.open(data)

	def test_heapdumpsegment_too_short(self):
		with self.hb.record(28, 123) as r:
			with r.subrecord(0xff) as s:
				s.id(123)
		with self.hb.record(1, 500) as r:
			r.id(567)
			r.bytes('Hello world!')
		addrs, data = self.hb.build()
		data[addrs[0] + 8] -= 1
		del data[addrs[1] - 1]
		data = bytes(data)
		with self.assertRaisesRegex(hprof.FileFormatError, '0x%x.*0x%x' % (10 + self.idsize, 9 + self.idsize)):
			hprof.open(data)
