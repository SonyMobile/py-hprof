import unittest
import hprof

class TestParseNameRecord(unittest.TestCase):

	def setUp(self):
		self.hf = hprof._parsing.HprofFile()
		self.hf.idsize = 4

	def callit(self, indata):
		reader = hprof._parsing.PrimitiveReader(memoryview(indata))
		hprof._parsing.record_parsers[0x01](self.hf, reader)

	def test_empty_name(self):
		self.callit(b'\x20\x30\x50\x43')
		self.assertIn(0x20305043, self.hf.names)
		self.assertEqual(self.hf.names[0x20305043], '')

	def test_swedish_name(self):
		self.callit(b'\x11\x15\x10\x55' + 'Hälge ÅÄÖsson'.encode('utf8'))
		self.assertIn(0x11151055, self.hf.names)
		self.assertEqual(self.hf.names[0x11151055], 'Hälge ÅÄÖsson')

	def test_japanese_name(self):
		self.callit(b'\x33\x32\x32\x32' + '山下さん'.encode('utf8'))
		self.assertIn(0x33323232, self.hf.names)
		self.assertEqual(self.hf.names[0x33323232], '山下さん')

	def test_4byte_utf8(self):
		self.callit(b'\x04\x14\x24\x34sil\xf0\x9f\x9c\x9bver')
		self.assertIn(0x04142434, self.hf.names)
		self.assertEqual(self.hf.names[0x04142434], 'sil🜛ver')

	def test_collision(self):
		self.callit(b'\x11\x15\x10\x55abc')
		with self.assertRaises(hprof.error.FormatError):
			self.callit(b'\x11\x15\x10\x55def')
		self.assertIn(0x11151055, self.hf.names)
		self.assertEqual(self.hf.names[0x11151055], 'abc')

	def test_multiple(self):
		self.callit(b'\x33\x32\x32\x32' + 'Hälge ÅÄÖsson'.encode('utf8'))
		self.callit(b'\x11\x15\x10\x55' + '山下さん'.encode('utf8'))
		self.assertIn(0x11151055, self.hf.names)
		self.assertIn(0x33323232, self.hf.names)
		self.assertEqual(self.hf.names[0x11151055], '山下さん')
		self.assertEqual(self.hf.names[0x33323232], 'Hälge ÅÄÖsson')

