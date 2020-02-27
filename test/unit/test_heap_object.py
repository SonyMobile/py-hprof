import unittest
import hprof

from unittest.mock import MagicMock, PropertyMock

from .util import varyingid, HeapRecordTest

@varyingid
class TestHeapObject(HeapRecordTest):
	def test_minimal(self):
		mock = MagicMock(
				_hprof_ifieldvals=PropertyMock(),
				__bases__ = (hprof.heap.JavaObject,))
		self.heap[0x2020] = mock
		self.doit(0x21, self.build()
				.id(0x0b1ec7) # object id
				.u4(0x57acc)  # stacktrace serial
				.id(0x2020)   # class id
				.u4(0x0)      # bytes remaining
		)
		self.assertEqual(mock.call_count, 1)
		self.assertEqual(mock.call_args[0], (self.id(0x0b1ec7),))
		self.assertEqual(mock.call_args[1], {})
		obj = self.heap[self.id(0x0b1ec7)]
		self.assertIs(obj, mock.return_value)
		mock._hprof_ifieldvals.assert_called_once_with(())

	def test_small(self):
		mock = MagicMock(
				_hprof_ifieldix = {'blah': 0},
				_hprof_ifields = {'blah': hprof.jtype.int},
				_hprof_ifieldvals=PropertyMock(),
				__bases__ = (hprof.heap.JavaObject,))
		self.heap[0x2021] = mock
		self.doit(0x21, self.build()
				.id(0x0b1ec7)   # object id
				.u4(0x57acc)    # stacktrace serial
				.id(0x2021)     # class id
				.u4(0x4)        # bytes remaining
				.u4(0x12345678) # first instance variable
		)
		self.assertEqual(mock.call_count, 1)
		self.assertEqual(mock.call_args[0], (self.id(0x0b1ec7),))
		self.assertEqual(mock.call_args[1], {})
		obj = self.heap[self.id(0x0b1ec7)]
		self.assertIs(obj, mock.return_value)
		mock._hprof_ifieldvals.assert_called_once_with((0x12345678,))

	def test_inherit(self):
		supermock = MagicMock(
				_hprof_ifieldix = {'blah': 0},
				_hprof_ifields = {'blah':  hprof.jtype.int},
				_hprof_ifieldvals=PropertyMock(),
				__bases__ = (hprof.heap.JavaObject,))
		mock = MagicMock(
				_hprof_ifieldix = {'some': 0, 'thing': 1},
				_hprof_ifields = {
					'some':  hprof.jtype.int,
					'thing': hprof.jtype.short,
				},
				_hprof_ifieldvals=PropertyMock(),
				__bases__ = (supermock,))
		self.heap[0x2021] = mock
		self.doit(0x21, self.build()
				.id(0x0b1ec6)   # object id
				.u4(0x57acca)   # stacktrace serial
				.id(0x2021)     # class id
				.u4(0xa)        # bytes remaining
				.u4(0x17273747) # first instance variable
				.u2(0x1314)     # second instance variable
				.u4(0x98979695) # first instance variable, super class
		)
		self.assertEqual(mock.call_count, 1)
		self.assertEqual(mock.call_args[0], (self.id(0x0b1ec6),))
		self.assertEqual(mock.call_args[1], {})
		obj = self.heap[self.id(0x0b1ec6)]
		self.assertIs(obj, mock.return_value)
		mock._hprof_ifieldvals.assert_called_once_with((0x17273747,0x1314))
		supermock._hprof_ifieldvals.assert_called_once_with((0x98979695-0x100000000,))
