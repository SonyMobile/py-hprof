# Copyright (C) 2019 Snild Dolkow
# Licensed under the LICENSE.

import unittest
import hprof

from .util import varyingid

@varyingid
class TestParseNameRecord(unittest.TestCase):

	def callit(self, indata):
		reader = hprof._parsing.PrimitiveReader(memoryview(indata), self.idsize)
		hprof._parsing.record_parsers[0x01](self.hf, reader, None)

	def test_empty_name(self):
		self.callit(self.build().id(0x20305043))
		nid = self.id(0x20305043)
		self.assertIn(nid, self.hf.names)
		self.assertEqual(self.hf.names[nid], '')

	def test_swedish_name(self):
		self.callit(self.build().id(0x11151055).utf8('Hälge ÅÄÖsson'))
		nid = self.id(0x11151055)
		self.assertIn(nid, self.hf.names)
		self.assertEqual(self.hf.names[nid], 'Hälge ÅÄÖsson')

	def test_japanese_name(self):
		self.callit(self.build().id(0x33323232).utf8('山下さん'))
		nid = self.id(0x33323232)
		self.assertIn(nid, self.hf.names)
		self.assertEqual(self.hf.names[nid], '山下さん')

	def test_4byte_utf8(self):
		self.callit(self.build().id(0x04142434).add(b'sil\xf0\x9f\x9c\x9bver'))
		nid = self.id(0x04142434)
		self.assertIn(nid, self.hf.names)
		self.assertEqual(self.hf.names[nid], 'sil🜛ver')

	def test_collision(self):
		self.callit(self.build().id(0x11151055).utf8('abc'))
		with self.assertRaises(hprof.error.FormatError):
			self.callit(self.build().id(0x11151055).utf8('def'))
		nid = self.id(0x11151055)
		self.assertIn(nid, self.hf.names)
		self.assertEqual(self.hf.names[nid], 'abc')

	def test_multiple(self):
		self.callit(self.build().id(0x33323232).utf8('Hälge ÅÄÖsson'))
		self.callit(self.build().id(0x11151055).utf8('山下さん'))
		hälge = self.id(0x33323232)
		yamashita = self.id(0x11151055)
		self.assertIn(yamashita, self.hf.names)
		self.assertIn(hälge, self.hf.names)
		self.assertEqual(self.hf.names[yamashita], '山下さん')
		self.assertEqual(self.hf.names[hälge], 'Hälge ÅÄÖsson')

