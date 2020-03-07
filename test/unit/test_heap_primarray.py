import unittest
import hprof

from unittest.mock import MagicMock

from .util import varyingid, HeapRecordTest

@varyingid
class TestPrimitiveArray(HeapRecordTest):

	def test_zero(self):
		self.heap._deferred_primarrays.append('dummy')
		self.doit(0x23, self.build()
				.id(0x0b1ec7) # array id
				.u4(0x57acc)  # stacktrace serial
				.u4(0x0)      # length
				.u1(4)        # element type (boolean)
		)
		self.assertEqual(len(self.heap._deferred_primarrays), 2)
		self.assertEqual(self.heap._deferred_primarrays[0], 'dummy')
		self.assertEqual(len(self.heap._deferred_primarrays[1]), 3)
		objid, strace, adata = self.heap._deferred_primarrays[1]
		self.assertEqual(objid, self.id(0x0b1ec7))
		self.assertEqual(strace, 0x57acc)
		self.assertIs(type(adata), hprof.heap._DeferredArrayData)
		self.assertIs(adata.jtype, hprof.jtype.boolean)
		self.assertEqual(adata.bytes, b'')

	def test_one(self):
		self.heap._deferred_primarrays.append('hello')
		self.heap._deferred_primarrays.append('world')
		self.doit(0x23, self.build()
				.id(0x0b1ec72)# array id
				.u4(0x57acc)  # stacktrace serial
				.u4(0x1)      # length
				.u1(9)        # element type (short)
				.u2(0xbea7)   # element 0
		)
		self.assertEqual(len(self.heap._deferred_primarrays), 3)
		self.assertEqual(self.heap._deferred_primarrays[0], 'hello')
		self.assertEqual(self.heap._deferred_primarrays[1], 'world')
		self.assertEqual(len(self.heap._deferred_primarrays[2]), 3)
		objid, strace, adata = self.heap._deferred_primarrays[2]
		self.assertEqual(objid, self.id(0x0b1ec72))
		self.assertEqual(strace, 0x57acc)
		self.assertIs(type(adata), hprof.heap._DeferredArrayData)
		self.assertIs(adata.jtype, hprof.jtype.short)
		self.assertEqual(adata.bytes, b'\xbe\xa7')

	def test_three(self):
		self.doit(0x23, self.build()
				.id(0x0b1ec72)# array id
				.u4(0x57acc)  # stacktrace serial
				.u4(0x3)      # length
				.u1(9)        # element type (short)
				.u2(0x5040)   # element 0
				.u2(0xbea7)   # element 1
				.u2(0x6677)   # element 2
		)
		self.assertEqual(len(self.heap._deferred_primarrays), 1)
		self.assertEqual(len(self.heap._deferred_primarrays[0]), 3)
		objid, strace, adata = self.heap._deferred_primarrays[0]
		self.assertEqual(objid, self.id(0x0b1ec72))
		self.assertIs(type(adata), hprof.heap._DeferredArrayData)
		self.assertIs(adata.jtype, hprof.jtype.short)
		self.assertEqual(adata.bytes, b'\x50\x40\xbe\xa7\x66\x77')

	def test_create_primarrays(self):
		fakes = (
			(1, 20, hprof.heap._DeferredArrayData(hprof.jtype.short, b'\x50\x40\xbe\xa7\x66\x77')),
			(5, 20, hprof.heap._DeferredArrayData(hprof.jtype.boolean, b'\x01')),
			(3, 10, hprof.heap._DeferredArrayData(hprof.jtype.short, b'')),
		)
		out1 = MagicMock()
		out2 = MagicMock()
		out3 = MagicMock()
		self.heap.classes['short[]']   = shortmock, = (MagicMock(side_effect=(out1, out2)),)
		self.heap.classes['boolean[]'] =  boolmock, = (MagicMock(side_effect=(out3,)),)
		self.heap._deferred_primarrays.extend(fakes)
		progress = MagicMock()

		hprof._heap_parsing.create_primarrays(self.heap, progress)

		self.assertEqual(shortmock.call_count, 2)
		self.assertEqual( boolmock.call_count, 1)
		self.assertEqual(len(self.heap._deferred_primarrays), 0)

		self.assertEqual(boolmock.call_args_list[0][0], (5,))
		self.assertEqual(boolmock.call_args_list[0][1], {})
		self.assertIn(5, self.heap)
		self.assertIs(self.heap[5], out3)
		self.assertIs(self.heap[5]._hprof_array_data, fakes[1][2])

		self.assertEqual(shortmock.call_args_list[0][0], (1,))
		self.assertEqual(shortmock.call_args_list[0][1], {})
		self.assertIn(1, self.heap)
		self.assertIs(self.heap[1], out1)
		self.assertIs(self.heap[1]._hprof_array_data, fakes[0][2])

		self.assertEqual(shortmock.call_args_list[1][0], (3,))
		self.assertEqual(shortmock.call_args_list[1][1], {})
		self.assertIn(3, self.heap)
		self.assertIs(self.heap[3], out2)
		self.assertIs(self.heap[3]._hprof_array_data, fakes[2][2])

		progress.assert_called_once_with(0)
