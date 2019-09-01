import unittest
import hprof

from unittest.mock import patch, MagicMock

class TestParseHeapRecord(unittest.TestCase):

	def test_empty(self):
		hf = hprof._parsing.HprofFile()
		self.assertEqual(len(hf.heaps), 0)
		reader = hprof._parsing.PrimitiveReader(b'', None)
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
		self.assertEqual(len(hf.heaps), 1)
		heap = hf.heaps[0]
		self.assertIsInstance(heap, hprof.heap.Heap)

		self.assertEqual(ph.call_count, 1)
		self.assertEqual(len(ph.call_args[0]), 2)
		self.assertIs(ph.call_args[0][0], heap)
		self.assertIs(ph.call_args[0][1], reader)
		self.assertCountEqual(ph.call_args[1], ())

		self.assertEqual(rhr.call_count, 1)
		self.assertEqual(len(rhr.call_args[0]), 1)
		self.assertIs(rhr.call_args[0][0], heap)
		self.assertCountEqual(ph.call_args[1], ())

	def test_heap_parser(self):
		dummies = {}
		dummies[1] = MagicMock(side_effect=lambda h,r: r.u(r.u(1)))
		dummies[2] = MagicMock()
		heap = hprof.heap.Heap()
		reader = hprof._parsing.PrimitiveReader(b'\2\2\2\1\3\6\6\6\2\1\2\4\3', None)
		with patch('hprof._heap_parsing.record_parsers', dummies):
			hprof._heap_parsing.parse_heap(heap, reader)
		self.assertEqual(dummies[1].call_count, 2)
		self.assertEqual(dummies[2].call_count, 4)
		self.assertCountEqual(dummies[1].call_args_list, 2 * (((heap, reader), {}),))
		self.assertCountEqual(dummies[2].call_args_list, 4 * (((heap, reader), {}),))

	def test_unhandled_heap_record(self):
		heap = hprof.heap.Heap()
		reader = hprof._parsing.PrimitiveReader(b'\x67\1\2\3\4\5', None)
		with self.assertRaisesRegex(hprof.error.FormatError, 'unrecognized heap record type 0x67'):
			hprof._heap_parsing.parse_heap(heap, reader)
