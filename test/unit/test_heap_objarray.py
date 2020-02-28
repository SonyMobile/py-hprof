import unittest
import hprof

from unittest.mock import MagicMock, PropertyMock

from .util import varyingid, HeapRecordTest

@varyingid
class TestObjectArray(HeapRecordTest):

	def test_minimal(self):
		mock = MagicMock()
		self.heap[0x1010] = mock
		self.doit(0x22, self.build()
				.id(0x0b1ec7) # array id
				.u4(0x57acc)  # stack trace serial
				.u4(0x0)      # length
				.id(0x1010)   # class id
		)
		self.assertEqual(mock.call_count, 1)
		self.assertEqual(mock.call_args[0], (self.id(0x0b1ec7),))
		self.assertEqual(mock.call_args[1], {})
		obj = self.heap[self.id(0x0b1ec7)]
		self.assertIs(obj, mock.return_value)
		self.assertEqual(obj._hprof_array_data, ())

	def test_small(self):
		mock = MagicMock(
				_hprof_ifieldvals=PropertyMock(),
				_hprof_array_data=PropertyMock(),
				__bases__ = (hprof.heap.JavaArray, hprof.heap.JavaObject))
		self.heap[0x1010] = mock
		self.doit(0x22, self.build()
				.id(0x0b1ec7) # array id
				.u4(0x57acc)  # stack trace serial
				.u4(0x1)      # length
				.id(0x1010)   # class id
				.id(0xf00baa) # element 0
		)
		self.assertEqual(mock.call_count, 1)
		self.assertEqual(mock.call_args[0], (self.id(0x0b1ec7),))
		self.assertEqual(mock.call_args[1], {})
		obj = self.heap[self.id(0x0b1ec7)]
		self.assertIs(obj, mock.return_value)
		self.assertEqual(obj._hprof_array_data, (self.id(0xf00baa),))

	def test_multi(self):
		mock = MagicMock(
				_hprof_ifieldvals=PropertyMock(),
				_hprof_array_data=PropertyMock(),
				__bases__ = (hprof.heap.JavaArray, hprof.heap.JavaObject))
		self.heap[0x1010] = mock
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
		self.assertEqual(mock.call_count, 1)
		self.assertEqual(mock.call_args[0], (self.id(0x0b1ec7),))
		self.assertEqual(mock.call_args[1], {})
		obj = self.heap[self.id(0x0b1ec7)]
		self.assertIs(obj, mock.return_value)
		self.assertEqual(obj._hprof_array_data, (
			self.id(0xbaabaa),
			self.id(0xf00f00),
			self.id(0xf00baa),
			self.id(0xbaaf00),
		))
