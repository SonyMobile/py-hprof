#!/usr/bin/env python3
#coding=utf8

from unittest import TestCase

import hprof

class TestArtificialHprof(TestCase):
	def setUp(self):
		self.data = [
			bytearray(b'JAVA PROFILE 1.0.3\0'),
			bytearray(b'\0\0\0\4'), # id size
			bytearray(b'\x00\x00\x01\x68\xE1\x43\xF2\x63'), # timestamp
			bytearray(b'\1\0\0\0\0\0\0\0\14Hello world!'),        # a utf8 string, "Hello world!"
			bytearray(b'\1\0\1\0\0\0\0\0\5\x50\xe5\xad\xa6\x51'), # a utf8 string, "P学Q"
			bytearray(b'\1\2\0\0\0\0\0\0\4ABBA'),                 # a utf8 string, "ABBA"
		]
		self.f = None

	def tearDown(self):
		self.close()

	def open(self):
		self.close()
		self.f = hprof.open(b''.join(self.data))

	def close(self):
		if self.f is not None:
			self.f.close()
			self.f = None

	def test_correct_header(self):
		self.open()
		self.assertEqual(self.f.idsize, 4)
		self.assertEqual(self.f.starttime_ms, 0x168E143F263)

	def test_correct_modified_header(self):
		self.data[1][3] = 8
		self.data[2][2] = 0
		self.data[2][7] = 0x64
		self.open()
		self.assertEqual(self.f.idsize, 8)
		self.assertEqual(self.f.starttime_ms, 0x68E143F264)

	def test_incorrect_header(self):
		self.data[0][7] = ord('Y')
		with self.assertRaisesRegex(hprof.FileFormatError, 'bad header'):
			self.open()

	def test_incorrect_version(self):
		self.data[0][13] = ord('9')
		with self.assertRaisesRegex(hprof.FileFormatError, 'bad version'):
			self.open()

	def test_list_0_records(self):
		self.data = self.data[:3]
		self.open()
		recs = list(self.f.records())
		self.assertEqual(len(recs), 0)

	def test_list_1_record(self):
		self.data = self.data[:4]
		self.open()
		recs = list(self.f.records())
		self.assertEqual(len(recs), 1)

	def test_list_2_records(self):
		self.data = self.data[:5]
		self.open()
		recs = list(self.f.records())
		self.assertEqual(len(recs), 2)

	def test_list_3_records(self):
		self.data = self.data[:6]
		self.open()
		recs = list(self.f.records())
		self.assertEqual(len(recs), 3)

	def test_read_utf8_records(self):
		self.data = self.data[:6]
		self.open()
		records = self.f.records()
		self.assertEqual(next(records).read(), 'Hello world!')
		self.assertEqual(next(records).read(), 'P学Q')
		self.assertEqual(next(records).read(), 'ABBA')
		with self.assertRaises(StopIteration):
			next(records)

	def test_record_length(self):
		self.open()
		records = self.f.records()
		self.assertEqual(len(next(records)), 21)
		self.assertEqual(len(next(records)), 14)
		self.assertEqual(len(next(records)), 13)

	def test_record_bodylen(self):
		self.open()
		records = self.f.records()
		self.assertEqual(next(records).bodylen, 12)
		self.assertEqual(next(records).bodylen, 5)
		self.assertEqual(next(records).bodylen, 4)

	def test_record_tags(self):
		self.open()
		for i, r in enumerate(self.f.records()):
			self.assertEqual(r.tag, self.data[3+i][0])

	def test_record_time(self):
		self.open()
		base = 0x168e143f263 * 1000
		records = self.f.records()
		self.assertEqual(next(records).timestamp_us, base + 0)
		self.assertEqual(next(records).timestamp_us, base + 0x10000)
		self.assertEqual(next(records).timestamp_us, base + 0x2000000)

	def test_record_bodyaddr(self):
		self.open()
		records = self.f.records()
		self.assertEqual(next(records).bodyaddr, 40)
		self.assertEqual(next(records).bodyaddr, 61)
		self.assertEqual(next(records).bodyaddr, 75)
