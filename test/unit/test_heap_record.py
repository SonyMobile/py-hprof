import unittest
import hprof

from unittest.mock import patch, MagicMock

class TestParseHeapRecord(unittest.TestCase):

	def test_empty(self):
		hf = hprof._parsing.HprofFile()
		progress = MagicMock()
		self.assertEqual(len(hf.heaps), 0)
		reader = hprof._parsing.PrimitiveReader(b'', None)
		hprof._parsing.record_parsers[0x0c](hf, reader, progress)
		self.assertEqual(len(hf.heaps), 1)
		heap, = hf.heaps
		self.assertEqual(len(heap), 0)
		self.assertEqual(progress.call_count, 0)

	def test_calls_heap_parser(self):
		def check_first(*args, **kwargs):
			self.assertEqual(rhr.call_count, 0)
		hf = hprof._parsing.HprofFile()
		progress = MagicMock()
		reader = 'I am a reader'
		with patch('hprof._heap_parsing.parse_heap', side_effect=check_first) as ph, patch('hprof._heap_parsing.resolve_heap_references') as rhr:
			hprof._parsing.record_parsers[0x0c](hf, reader, progress)
		self.assertEqual(len(hf.heaps), 1)
		heap = hf.heaps[0]
		self.assertIsInstance(heap, hprof.heap.Heap)

		self.assertEqual(ph.call_count, 1)
		self.assertEqual(len(ph.call_args[0]), 4)
		self.assertIs(ph.call_args[0][0], hf)
		self.assertIs(ph.call_args[0][1], heap)
		self.assertIs(ph.call_args[0][2], reader)
		self.assertIs(ph.call_args[0][3], progress)
		self.assertCountEqual(ph.call_args[1], ())

		self.assertEqual(rhr.call_count, 1)
		self.assertEqual(len(rhr.call_args[0]), 1)
		self.assertIs(rhr.call_args[0][0], heap)
		self.assertCountEqual(ph.call_args[1], ())

		self.assertEqual(progress.call_count, 0)

	def test_heap_parser(self):
		dummies = {}
		dummies[1] = MagicMock(side_effect=lambda f,h,r: r.bytes(r.u1()))
		dummies[2] = MagicMock()
		progress = MagicMock()
		hf = hprof._parsing.HprofFile()
		heap = hprof.heap.Heap()
		reader = hprof._parsing.PrimitiveReader(b'\2\2\2\1\3\6\6\6\2\1\2\4\3', None)
		with patch('hprof._heap_parsing.record_parsers', dummies):
			hprof._heap_parsing.parse_heap(hf, heap, reader, progress)
		self.assertEqual(dummies[1].call_count, 2)
		self.assertEqual(dummies[2].call_count, 4)
		self.assertCountEqual(dummies[1].call_args_list, 2 * (((hf, heap, reader), {}),))
		self.assertCountEqual(dummies[2].call_args_list, 4 * (((hf, heap, reader), {}),))
		self.assertEqual(progress.call_count, 0)

	def test_unhandled_heap_record(self):
		hf = hprof._parsing.HprofFile()
		progress = MagicMock()
		heap = hprof.heap.Heap()
		reader = hprof._parsing.PrimitiveReader(b'\x67\1\2\3\4\5', None)
		with self.assertRaisesRegex(hprof.error.FormatError, 'unrecognized heap record type 0x67'):
			hprof._heap_parsing.parse_heap(hf, heap, reader, progress)
		self.assertEqual(progress.call_count, 0)

	def test_big_arrays_progress(self):
		from math import ceil
		hf = hprof._parsing.HprofFile()
		heap = hprof.heap.Heap()
		heap.classes['long[]'] = [MagicMock()]
		data = bytearray()
		while len(data) <= (3 << 20) + 20000:
			before = len(data)
			data.extend(b'\x23\0\0\0\1\0\0\0\2\0\0\2\0\13')
			for i in range(0x200):
				data.extend(b'\0\0\0\0\0\0\0\0')
			incr = len(data) - before
		expected1 = ceil((1<<20) / incr) * incr + 1
		expected2 = expected1 + ceil((1<<20) / incr) * incr
		expected3 = expected2 + ceil((1<<20) / incr) * incr
		for progress in (None, MagicMock()):
			with self.subTest(progress_callback = progress):
				reader = hprof._parsing.PrimitiveReader(memoryview(data), 4)
				hprof._heap_parsing.parse_heap(hf, heap, reader, progress)
				if progress:
					self.assertEqual(progress.call_count, 3)
					self.assertEqual(progress.call_args_list[0][0], (expected1,))
					self.assertEqual(progress.call_args_list[0][1], {})
					self.assertEqual(progress.call_args_list[1][0], (expected2,))
					self.assertEqual(progress.call_args_list[1][1], {})
					self.assertEqual(progress.call_args_list[2][0], (expected3,))
					self.assertEqual(progress.call_args_list[2][1], {})
