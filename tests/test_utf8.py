#!/usr/bin/env python3
#coding=utf8

from datetime import datetime, timedelta
from unittest import TestCase

import hprof

class TestUtf8(TestCase):
	def setUp(self):
		self.data = [
			bytearray(b'JAVA PROFILE 1.0.3\0'),
			bytearray(b'\0\0\0\4'), # id size
			bytearray(b'\x00\x00\x01\x68\xE1\x43\xF2\x63'), # timestamp
			bytearray(b'\1\0\0\0\0\0\0\0\20\0\1\2\3Hello world!'),         # a utf8 string, "Hello world!", id=0x00010203
			bytearray(b'\1\0\1\0\0\0\0\0\11\3\2\1\1\x50\xe5\xad\xa6\x51'), # a utf8 string, "P学Q", id=0x03020101
			bytearray(b'\1\2\0\0\0\0\0\0\10\3\4\5\6ABBA'),                 # a utf8 string, "ABBA", id=0x03040506
		]
		self.f = hprof.open(b''.join(self.data))
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
		self.assertEqual(next(records).str, 'ABBA')

	### generic record fields ###

	def test_utf8_addr(self):
		self.assertEqual(next(self.recs).addr, 31)
		self.assertEqual(next(self.recs).addr, 56)
		self.assertEqual(next(self.recs).addr, 74)

	def test_utf8_id(self):
		self.assertEqual(next(self.recs).id, 0x10203)
		self.assertEqual(next(self.recs).id, 0x3020101)
		self.assertEqual(next(self.recs).id, 0x3040506)

	def test_utf8_type(self):
		self.assertIs(type(next(self.recs)), hprof.record.Utf8)
		self.assertIs(type(next(self.recs)), hprof.record.Utf8)
		self.assertIs(type(next(self.recs)), hprof.record.Utf8)

	def test_utf8_tag(self):
		self.assertEqual(next(self.recs).tag, 1)
		self.assertEqual(next(self.recs).tag, 1)
		self.assertEqual(next(self.recs).tag, 1)

	def test_utf8_timestamp(self):
		self.assertEqual(next(self.recs).timestamp, datetime.fromtimestamp(0x168e143f263 / 1000))
		self.assertEqual(next(self.recs).timestamp, datetime.fromtimestamp(0x168e143f263 / 1000 + 0x10000 / 1000000))
		self.assertEqual(next(self.recs).timestamp, datetime.fromtimestamp(0x168e143f263 / 1000 + 0x2000000 / 1000000))

	def test_utf8_relative_timestamp(self):
		self.assertEqual(next(self.recs).relative_timestamp, timedelta(microseconds=0))
		self.assertEqual(next(self.recs).relative_timestamp, timedelta(microseconds=0x10000))
		self.assertEqual(next(self.recs).relative_timestamp, timedelta(microseconds=0x2000000))

	def test_utf8_rawbody(self):
		self.assertEqual(next(self.recs).rawbody, self.data[3][9:])
		self.assertEqual(next(self.recs).rawbody, self.data[4][9:])
		self.assertEqual(next(self.recs).rawbody, self.data[5][9:])

	def test_utf8_len(self):
		self.assertEqual(len(next(self.recs)), 25)
		self.assertEqual(len(next(self.recs)), 18)
		self.assertEqual(len(next(self.recs)), 17)
