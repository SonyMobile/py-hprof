import unittest
import hprof

from .util import varyingid

@varyingid
class TestParseHeapRecord(unittest.TestCase):

	def parse(self, data):
		reader = hprof._parsing.PrimitiveReader(memoryview(data))
		hprof._parsing.record_parsers[0x0c](self.hf, reader)

	def test_empty(self):
		self.parse(b'')
		self.assertEqual(len(self.hf.heaps), 1)
		heap, = self.hf.heaps
		# TODO: test that lots of functions return sensible values.
