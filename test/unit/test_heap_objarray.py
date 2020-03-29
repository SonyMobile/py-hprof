# Copyright (C) 2019 Snild Dolkow
# Licensed under the LICENSE.

import unittest
import hprof

from unittest.mock import MagicMock, PropertyMock

from .util import varyingid, HeapRecordTest

@varyingid
class TestObjectArray(HeapRecordTest):

	def test_minimal(self):
		self.doit(0x22, self.build()
				.id(0x0b1ec7) # array id
				.u4(0x57acc)  # stack trace serial
				.u4(0x0)      # length
				.id(0x1010)   # class id
		)
		expected = [(self.id(0x0b1ec7), 0x57acc, self.id(0x1010), ())]
		self.assertEqual(self.heap._deferred_objarrays, expected)

	def test_small(self):
		self.doit(0x22, self.build()
				.id(0x0b1ec7) # array id
				.u4(0x57acc)  # stack trace serial
				.u4(0x1)      # length
				.id(0x1010)   # class id
				.id(0xf00baa) # element 0
		)
		expected = [(self.id(0x0b1ec7), 0x57acc, self.id(0x1010), (self.id(0xf00baa),))]
		self.assertEqual(self.heap._deferred_objarrays, expected)

	def test_multi(self):
		self.heap._deferred_objarrays.append('hello')
		self.heap._deferred_objarrays.append('world')
		self.doit(0x22, self.build()
				.id(0x0b1ec7) # array id
				.u4(0x57acc)  # stack trace serial
				.u4(0x4)      # length
				.id(0x1010)   # class id
				.id(0xbaabaa) # element 0
				.id(0xf00f00) # element 1
				.id(0xf00baa) # element 2
				.id(0xbaaf00) # element 3
		)
		expected = [
				'hello',
				'world',
				(self.id(0x0b1ec7), 0x57acc, self.id(0x1010), (self.id(0xbaabaa),self.id(0xf00f00),self.id(0xf00baa),self.id(0xbaaf00)))
		]
		self.assertEqual(self.heap._deferred_objarrays, expected)

	def test_create_objarrays(self):
		fakes = (
			(99, 55, 10, (11,12,13)),
			(79, 45, 11, (22,21,20)),
			(78, 55, 10, (12,13,14,15)),
		)
		out1 = MagicMock()
		out2 = MagicMock()
		out3 = MagicMock()
		self.heap[10] = cls1 = MagicMock(side_effect=(out1,out2))
		self.heap[11] = cls2 = MagicMock(side_effect=(out3,))
		self.heap._deferred_objarrays.extend(fakes)
		self.heap._instances[cls1] = []
		self.heap._instances[cls2] = []
		progress = MagicMock()

		hprof._heap_parsing.create_objarrays(self.heap, progress)

		self.assertEqual(cls1.call_count, 2)
		self.assertEqual(cls2.call_count, 1)
		self.assertEqual(len(self.heap._deferred_objarrays), 0)

		self.assertEqual(cls1.call_args_list[0][0], (99,))
		self.assertEqual(cls1.call_args_list[0][1], {})
		self.assertIn(99, self.heap)
		self.assertIs(self.heap[99], out1)
		self.assertIs(self.heap[99]._hprof_array_data, fakes[0][3])

		self.assertEqual(cls1.call_args_list[1][0], (78,))
		self.assertEqual(cls1.call_args_list[1][1], {})
		self.assertIn(78, self.heap)
		self.assertIs(self.heap[78], out2)
		self.assertIs(self.heap[78]._hprof_array_data, fakes[2][3])

		self.assertEqual(cls2.call_args_list[0][0], (79,))
		self.assertEqual(cls2.call_args_list[0][1], {})
		self.assertIn(79, self.heap)
		self.assertIs(self.heap[79], out3)
		self.assertIs(self.heap[79]._hprof_array_data, fakes[1][3])

		self.assertCountEqual(self.heap._instances[cls1], (out1, out2))
		self.assertCountEqual(self.heap._instances[cls2], (out3,))

		progress.assert_called_once_with(0)
