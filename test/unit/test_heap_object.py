import unittest
import hprof

from unittest.mock import MagicMock, PropertyMock

from .util import varyingid, HeapRecordTest

@varyingid
class TestHeapObject(HeapRecordTest):
	def test_minimal(self):
		self.doit(0x21, self.build()
				.id(0x0b1ec7) # object id
				.u4(0x57acc)  # stacktrace serial
				.id(0x2020)   # class id
				.u4(0x0)      # bytes remaining
		)
		expected = [(self.id(0x0b1ec7), 0x57acc, self.id(0x2020), b'')]
		self.assertEqual(self.heap._deferred_objects, expected)

	def test_small(self):
		self.doit(0x21, self.build()
				.id(0x0b1ec7)   # object id
				.u4(0x57acc)    # stacktrace serial
				.id(0x2021)     # class id
				.u4(0x4)        # bytes remaining
				.u4(0x12345678) # first instance variable
		)
		expected = [(self.id(0x0b1ec7), 0x57acc, self.id(0x2021), b'\x12\x34\x56\x78')]
		self.assertEqual(self.heap._deferred_objects, expected)

	def test_multi(self):
		self.heap._deferred_objects.append('hello')
		self.heap._deferred_objects.append('world')
		self.doit(0x21, self.build()
				.id(0x0b1ec6)   # object id
				.u4(0x57acca)   # stacktrace serial
				.id(0x2021)     # class id
				.u4(0xa)        # bytes remaining
				.u4(0x17273747) # first instance variable
				.u2(0x1314)     # second instance variable
				.u4(0x98979695) # first instance variable, super class
		)
		expected = [
			'hello',
			'world',
			(self.id(0x0b1ec6), 0x57acca, self.id(0x2021), b'\x17\x27\x37\x47\x13\x14\x98\x97\x96\x95')
		]
		self.assertEqual(self.heap._deferred_objects, expected)

	def test_create_objects(self):
		cls0attr = MagicMock(
				_hprof_ifieldvals=PropertyMock(),
				__bases__ = (hprof.heap.JavaObject,))
		cls1attr = MagicMock(
				_hprof_ifieldix = {'blah': 0},
				_hprof_ifields = {'blah': hprof.jtype.object},
				_hprof_ifieldvals=PropertyMock(),
				__bases__ = (hprof.heap.JavaObject,))
		cls3attr = MagicMock(
				_hprof_ifieldix = {'some': 0, 'thing': 1},
				_hprof_ifields = {
					'some':  hprof.jtype.int,
					'thing': hprof.jtype.short,
				},
				_hprof_ifieldvals=PropertyMock(),
				__bases__ = (cls1attr,)) # inherits from cls1attr
		self.heap[0x2020] = cls0attr
		self.heap[0x2021] = cls1attr
		self.heap[0x2022] = cls3attr
		self.heap._instances[cls0attr] = []
		self.heap._instances[cls1attr] = []
		self.heap._instances[cls3attr] = []

		fakes = (
			(0x0b1ec7, 0x57acc,  0x2020, b''),
			(0x0b1ec6, 0x57acc,  0x2021, self.build().id(0x12345678)),
			(0x0b1ec5, 0x57acca, 0x2022, self.build().i4(0x98979695).u2(0x1314).id(0xabcd0123f)),
		)
		self.heap._deferred_objects.extend(fakes)
		progress = MagicMock()

		hprof._heap_parsing.create_instances(self.heap, self.idsize, progress)

		with self.subTest('0 attrs'):
			self.assertEqual(cls0attr.call_count, 1)
			self.assertEqual(cls0attr.call_args[0], (0x0b1ec7,))
			self.assertEqual(cls0attr.call_args[1], {})
			obj = self.heap[0x0b1ec7]
			self.assertIs(obj, cls0attr.return_value)
			cls0attr._hprof_ifieldvals.assert_called_once_with(())
			self.assertCountEqual(self.heap._instances[cls0attr], (obj,))

		with self.subTest('1 attr'):
			self.assertEqual(cls1attr.call_count, 1)
			self.assertEqual(cls1attr.call_args_list[0][0], (0x0b1ec6,))
			self.assertEqual(cls1attr.call_args_list[0][1], {})
			obj = self.heap[0x0b1ec6]
			self.assertIs(obj, cls1attr.return_value)
			self.assertGreaterEqual(cls1attr._hprof_ifieldvals.call_count, 1)
			self.assertEqual(cls1attr._hprof_ifieldvals.call_args_list[0][0], ((self.id(0x12345678),),))
			self.assertCountEqual(self.heap._instances[cls1attr], (obj,))

		with self.subTest('3 attrs'):
			self.assertEqual(cls3attr.call_count, 1)
			self.assertEqual(cls3attr.call_args_list[0][0], (0x0b1ec5,))
			self.assertEqual(cls3attr.call_args_list[0][1], {})
			obj = self.heap[0x0b1ec5]
			self.assertIs(obj, cls3attr.return_value)
			cls3attr._hprof_ifieldvals.assert_called_once_with((0x98979695-0x100000000,0x1314))
			self.assertEqual(cls1attr._hprof_ifieldvals.call_count, 2)
			self.assertEqual(cls1attr._hprof_ifieldvals.call_args_list[1][0], ((self.id(0xabcd0123f),),))
			self.assertCountEqual(self.heap._instances[cls3attr], (obj,))

		self.assertEqual(len(self.heap._deferred_objects), 0)
		progress.assert_called_once_with(0)
