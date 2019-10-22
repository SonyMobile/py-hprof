import unittest
import hprof

from unittest.mock import MagicMock

from .util import varyingid, HeapRecordTest

@varyingid
class TestPrimitiveArray(HeapRecordTest):

	def test_zero(self):
		mock = MagicMock()
		self.heap[1010] = mock
		self.heap.classes['boolean[]'] = [mock]
		self.doit(0x23, self.build()
				.id(0x0b1ec7) # array id
				.u4(0x57acc)  # stacktrace serial
				.u4(0x0)      # length
				.u1(4)        # element type (boolean)
		)
		self.assertEqual(mock.call_count, 1)
		self.assertEqual(mock.call_args[0], (self.id(0x0b1ec7),))
		self.assertEqual(mock.call_args[1], {})
		arr = self.heap[self.id(0x0b1ec7)]
		self.assertIs(arr, mock.return_value)
		adata = arr._hprof_array_data
		self.assertIs(type(adata), hprof.heap._DeferredArrayData)
		self.assertIs(adata.jtype, hprof.jtype.boolean)
		self.assertEqual(adata.bytes, b'')

	def test_one(self):
		mock = MagicMock()
		self.heap[1022] = mock
		self.heap.classes['short[]'] = [mock]
		self.doit(0x23, self.build()
				.id(0x0b1ec72)# array id
				.u4(0x57acc)  # stacktrace serial
				.u4(0x1)      # length
				.u1(9)        # element type (short)
				.u2(0xbea7)   # element 0
		)
		self.assertEqual(mock.call_count, 1)
		self.assertEqual(mock.call_args[0], (self.id(0x0b1ec72),))
		self.assertEqual(mock.call_args[1], {})
		arr = self.heap[self.id(0x0b1ec72)]
		self.assertIs(arr, mock.return_value)
		adata = arr._hprof_array_data
		self.assertIs(type(adata), hprof.heap._DeferredArrayData)
		self.assertIs(adata.jtype, hprof.jtype.short)
		self.assertEqual(adata.bytes, b'\xbe\xa7')

	def test_three(self):
		mock = MagicMock()
		self.heap[1234] = mock
		self.heap.classes['short[]'] = [mock]
		self.doit(0x23, self.build()
				.id(0x0b1ec72)# array id
				.u4(0x57acc)  # stacktrace serial
				.u4(0x3)      # length
				.u1(9)        # element type (short)
				.u2(0x5040)   # element 0
				.u2(0xbea7)   # element 1
				.u2(0x6677)   # element 2
		)
		self.assertEqual(mock.call_count, 1)
		self.assertEqual(mock.call_args[0], (self.id(0x0b1ec72),))
		self.assertEqual(mock.call_args[1], {})
		arr = self.heap[self.id(0x0b1ec72)]
		self.assertIs(arr, mock.return_value)
		adata = arr._hprof_array_data
		self.assertIs(type(adata), hprof.heap._DeferredArrayData)
		self.assertIs(adata.jtype, hprof.jtype.short)
		self.assertEqual(adata.bytes, b'\x50\x40\xbe\xa7\x66\x77')
