# Copyright (C) 2019 Sony Mobile Communications Inc.
# Licensed under the LICENSE

from datetime import datetime, timedelta
from unittest import TestCase

import hprof

from .util import HprofBuilder, varying_idsize

@varying_idsize
class TestUtf8(TestCase):
	def setUp(self):
		builder = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 0x168e143f263)
		with builder.record(1, 0) as r:
			r.id(0x0203)
			r.bytes('Hello world!')
		with builder.record(1, 0x10000)  as r:
			r.id(0x0101)
			r.bytes('P学Q')
		with builder.record(1, 0x2000000) as r:
			r.id(0x0506)
			r.bytes('A\r𣲷\nB')
		self.addr, self.data = builder.build()
		self.f = hprof.open(bytes(self.data))
		self.recs = self.f.records()

	def tearDown(self):
		self.f.close()
		self.f = None
		self.recs = None

	### type-specific fields ###

	def test_utf8_string(self):
		records = self.f.records()
		self.assertEqual(next(records).str, 'Hello world!')
		self.assertEqual(next(records).str, 'P学Q')
		self.assertEqual(next(records).str, 'A\r𣲷\nB')

	### generic record fields ###

	def test_utf8_addr(self):
		self.assertEqual(next(self.recs).hprof_addr, 31)
		self.assertEqual(next(self.recs).hprof_addr, 52 + self.idsize)
		self.assertEqual(next(self.recs).hprof_addr, 66 + 2 * self.idsize)

	def test_utf8_id(self):
		self.assertEqual(next(self.recs).id, 0x0203)
		self.assertEqual(next(self.recs).id, 0x0101)
		self.assertEqual(next(self.recs).id, 0x0506)

	def test_utf8_type(self):
		self.assertIs(type(next(self.recs)), hprof.record.Utf8)
		self.assertIs(type(next(self.recs)), hprof.record.Utf8)
		self.assertIs(type(next(self.recs)), hprof.record.Utf8)

	def test_utf8_timestamp(self):
		self.assertEqual(next(self.recs).timestamp, datetime.fromtimestamp(0x168e143f263 / 1000))
		self.assertEqual(next(self.recs).timestamp, datetime.fromtimestamp(0x168e143f263 / 1000 + 0x10000 / 1000000))
		self.assertEqual(next(self.recs).timestamp, datetime.fromtimestamp(0x168e143f263 / 1000 + 0x2000000 / 1000000))

	def test_utf8_relative_timestamp(self):
		self.assertEqual(next(self.recs).relative_timestamp, timedelta(microseconds=0))
		self.assertEqual(next(self.recs).relative_timestamp, timedelta(microseconds=0x10000))
		self.assertEqual(next(self.recs).relative_timestamp, timedelta(microseconds=0x2000000))

	def test_utf8_rawbody(self):
		self.assertEqual(next(self.recs).rawbody, self.data[self.addr[0] + 9:self.addr[1]])
		self.assertEqual(next(self.recs).rawbody, self.data[self.addr[1] + 9:self.addr[2]])
		self.assertEqual(next(self.recs).rawbody, self.data[self.addr[2] + 9:len(self.data)])

	def test_utf8_len(self):
		self.assertEqual(next(self.recs)._hprof_len, 21 + self.idsize)
		self.assertEqual(next(self.recs)._hprof_len, 14 + self.idsize)
		self.assertEqual(next(self.recs)._hprof_len, 17 + self.idsize)

	def test_utf8_str(self):
		self.assertEqual(str(next(self.recs)), 'Hello world!')
		self.assertEqual(str(next(self.recs)), 'P学Q')
		self.assertEqual(str(next(self.recs)), 'A\r𣲷\nB')
