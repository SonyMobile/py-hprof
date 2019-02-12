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
		self.assertEqual(self.f.starttime, 0x168E143F263)

	def test_correct_modified_header(self):
		self.data[1][3] = 8
		self.data[2][2] = 0
		self.data[2][7] = 0x64
		self.open()
		self.assertEqual(self.f.idsize, 8)
		self.assertEqual(self.f.starttime, 0x68E143F264)

	def test_incorrect_header(self):
		self.data[0][7] = ord('Y')
		with self.assertRaisesRegex(hprof.FileFormatError, 'bad header'):
			self.open()

	def test_incorrect_version(self):
		self.data[0][13] = ord('9')
		with self.assertRaisesRegex(hprof.FileFormatError, 'bad version'):
			self.open()
