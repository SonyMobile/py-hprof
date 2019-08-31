import unittest
import hprof

from unittest.mock import patch

class TestParseHeapRecord(unittest.TestCase):

	def test_empty(self):
		hf = hprof._parsing.HprofFile()
		self.assertEqual(len(hf.heaps), 0)
		reader = hprof._parsing.PrimitiveReader(b'', 4)
		hprof._parsing.record_parsers[0x0c](hf, reader)
		self.assertEqual(len(hf.heaps), 1)
		heap, = hf.heaps
		self.assertEqual(len(heap.objects), 0)

	def test_calls_heap_parser(self):
		def check_first(*args, **kwargs):
			self.assertEqual(rhr.call_count, 0)
		hf = hprof._parsing.HprofFile()
		reader = 'I am a reader'
		with patch('hprof._heap_parsing.parse_heap', side_effect=check_first) as ph, patch('hprof._heap_parsing.resolve_heap_references') as rhr:
			hprof._parsing.record_parsers[0x0c](hf, reader)
		self.assertEqual(ph.call_count, 1)
		self.assertEqual(len(ph.call_args[0]), 2)
		heap = ph.call_args[0][0]
		self.assertIsInstance(heap, hprof.heap.Heap)
		self.assertIs(ph.call_args[0][1], reader)
		self.assertCountEqual(ph.call_args[1], ())
		self.assertEqual(rhr.call_count, 1)
