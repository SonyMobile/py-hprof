# Copyright (C) 2019 Snild Dolkow
# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

import unittest
import hprof

from unittest.mock import patch

from .util import varyingid, HeapRecordTest

@varyingid
class TestHeapClass(HeapRecordTest):

	def test_class_class(self):
		load = hprof._parsing.ClassLoad()
		load.class_id = self.id(0xc1a55)
		load.class_name = 'java/lang/Class'
		self.hf.classloads_by_id[load.class_id] = load

		self.doit(0x20, self.build()
				.id(0xc1a55)   # class object id
				.u4(0x57acc)   # stacktrace serial
				.id(0)         # superclass id (null)
				.id(0x10ade2)  # loader id
				.id(0x5151515) # signer id
				.id(0x5ec002e) # protection domain id
				.id(0x999999)  # reserved 1
				.id(0xaaaaaa)  # reserved 2
				.u4(0x40)      # instance size
				.u2(0x0)       # constant pool size
				.u2(0x0)       # static field count
				.u2(0x0)       # instance field count
		)
		cls = self.heap[self.id(0xc1a55)]
		self.assertEqual(str(cls), 'java.lang.Class')
		self.assertEqual(self.heap.classtree.java.lang.Class, 'java.lang.Class')
		self.assertIn(self.heap.classtree.java.lang.Class, self.heap.classes)
		matches = self.heap.classes[self.heap.classtree.java.lang.Class]
		self.assertEqual(matches, [cls])
		self.assertEqual(self.heap._instances[cls], [])

	def test_minimal(self):
		expected = object()
		load = hprof._parsing.ClassLoad()
		load.class_id = self.id(0x7e577e57)
		load.class_name = 'java/lang/String'
		self.hf.classloads_by_id[load.class_id] = load
		self.heap[0x0b1ec7] = obj = object()

		with patch('hprof.heap._create_class', return_value=('java.lang.String', expected)) as mock:
			self.doit(0x20, self.build()
					.id(0x7e577e57) # class object id
					.u4(0x123)      # stacktrace serial
					.id(0x0b1ec7)   # superclass id
					.id(0x10ade2)   # loader id
					.id(0x5151515)  # signer id
					.id(0x5ec002e)  # protection domain id
					.id(0x999999)   # reserved 1
					.id(0xaaaaaa)   # reserved 2
					.u4(0x40)       # instance size
					.u2(0x0)        # constant pool size
					.u2(0x0)        # static field count
					.u2(0x0)        # instance field count
			)
		self.assertEqual(mock.call_count, 1)
		self.assertEqual(mock.call_args, (
			(self.heap.classtree, 'java/lang/String', obj, {}, (), ()),
			{},
		))
		cid = self.id(0x7e577e57)
		self.assertIn(cid, self.heap)
		self.assertIs(self.heap[cid], expected)
		self.assertIn('java.lang.String', self.heap.classes)
		self.assertEqual(self.heap.classes['java.lang.String'], [expected])
		self.assertEqual(self.heap._instances[expected], [])

	def test_small(self):
		expected = object()
		load = hprof._parsing.ClassLoad()
		load.class_id = self.id(0x7e577e57)
		load.class_name = 'java/lang/String'
		self.hf.classloads_by_id[load.class_id] = load
		self.hf.names[0xf00] = 'foo'
		self.hf.names[0xbaa] = 'bar'
		self.heap[0x0b1ec7] = obj = object()

		with patch('hprof.heap._create_class', return_value=('java.lang.String', expected)) as mock:
			self.doit(0x20, self.build()
					.id(0x7e577e57) # class object id
					.u4(0x123)      # stacktrace serial
					.id(0x0b1ec7)   # superclass id
					.id(0x10ade2)   # loader id
					.id(0x5151515)  # signer id
					.id(0x5ec002e)  # protection domain id
					.id(0x999999)   # reserved 1
					.id(0xaaaaaa)   # reserved 2
					.u4(0x40)       # instance size
					.u2(0x1)        # constant pool size
						.u2(0x0)    # constant pool index
						.u1(4)      # type (boolean)
						.u1(1)      # value (true)
					.u2(0x1)        # static field count
						.id(0xf00)  # field name
						.u1(11)     # field type (long)
						.u8(70000)  # field value
					.u2(0x1)        # instance field count
						.id(0xbaa)  # field name
						.u1(10)     # field type (int)
			)
		self.assertEqual(mock.call_count, 1)
		self.assertEqual(len(mock.call_args[0]), 6)
		self.assertIs(   mock.call_args[0][0], self.heap.classtree)
		self.assertEqual(mock.call_args[0][1], 'java/lang/String')
		self.assertIs(   mock.call_args[0][2], obj)
		self.assertEqual(mock.call_args[0][3], {'foo': 70000})
		self.assertEqual(mock.call_args[0][4], ('bar',))
		self.assertEqual(mock.call_args[0][5], (hprof.jtype.int,))
		self.assertEqual(mock.call_args[1], {})
		cid = self.id(0x7e577e57)
		self.assertIn(cid, self.heap)
		self.assertIs(self.heap[cid], expected)
		self.assertIn('java.lang.String', self.heap.classes)
		self.assertEqual(self.heap.classes['java.lang.String'], [expected])
		self.assertEqual(self.heap._instances[expected], [])

	def test_duplicate_class(self):
		load = hprof._parsing.ClassLoad()
		load.class_id = self.id(0x7e577e57)
		load.class_name = 'java/lang/String'
		self.hf.classloads_by_id[load.class_id] = load
		self.hf.names[0xf00] = 'foo'
		self.hf.names[0xbaa] = 'bar'

		self.heap[self.id(0x7e577e57)] = 'other object'

		data = (self.build()
				.id(0x7e577e57) # class object id
				.u4(0x124)      # stacktrace serial
				.id(0x0b1ec7)   # superclass id
				.id(0x10ade2)   # loader id
				.id(0x5151515)  # signer id
				.id(0x5ec002e)  # protection domain id
				.id(0x999999)   # reserved 1
				.id(0xaaaaaa)   # reserved 2
				.u4(0x40)       # instance size
				.u2(0x0)        # constant pool size
				.u2(0x0)        # static field count
				.u2(0x0)        # instance field count
		)
		with patch('hprof.heap._create_class', return_value=('java.lang.String', None)) as mock:
			with self.assertRaisesRegex(hprof.error.FormatError, 'duplicate'):
				self.doit(0x20, data)
		self.assertEqual(self.heap[self.id(0x7e577e57)], 'other object')
		with self.assertRaises(KeyError):
			self.heap.classes['java.lang.String']
		ct = self.heap.classtree
		with self.assertRaises(AttributeError):
			ct.java

	def test_duplicate_classname(self):
		expected1 = object()
		expected2 = object()
		load = hprof._parsing.ClassLoad()
		load.class_id = self.id(0x7e577e57)
		load.class_name = 'java/lang/String'
		self.hf.classloads_by_id[load.class_id] = load
		load = hprof._parsing.ClassLoad()
		load.class_id = self.id(0x7e577e56)
		load.class_name = 'java/lang/String'
		self.hf.classloads_by_id[load.class_id] = load
		self.hf.names[0xf00] = 'foo'
		self.hf.names[0xbaa] = 'bar'
		self.heap[0x0b1ec7] = obj = object()

		with patch('hprof.heap._create_class', return_value=('java.lang.String', expected1)) as mock:
			data = (self.build()
					.id(0x7e577e57) # class object id
					.u4(0x124)      # stacktrace serial
					.id(0x0b1ec7)   # superclass id
					.id(0x10ade2)   # loader id
					.id(0x5151515)  # signer id
					.id(0x5ec002e)  # protection domain id
					.id(0x999999)   # reserved 1
					.id(0xaaaaaa)   # reserved 2
					.u4(0x40)       # instance size
					.u2(0x0)        # constant pool size
					.u2(0x0)        # static field count
					.u2(0x0)        # instance field count
			)
			self.doit(0x20, data)
		with patch('hprof.heap._create_class', return_value=('java.lang.String', expected2)) as mock:
			data = (self.build()
					.id(0x7e577e56) # class object id
					.u4(0x124)      # stacktrace serial
					.id(0x0b1ec7)   # superclass id
					.id(0x10ade2)   # loader id
					.id(0x5151515)  # signer id
					.id(0x5ec002e)  # protection domain id
					.id(0x999999)   # reserved 1
					.id(0xaaaaaa)   # reserved 2
					.u4(0x40)       # instance size
					.u2(0x0)        # constant pool size
					.u2(0x0)        # static field count
					.u2(0x0)        # instance field count
			)
			self.doit(0x20, data)
		self.assertCountEqual(self.heap.classes['java.lang.String'], (expected1, expected2))
		self.assertEqual(self.heap._instances[expected1], [])
		self.assertEqual(self.heap._instances[expected2], [])

	def test_super_after_subclass(self):
		load = hprof._parsing.ClassLoad()
		load.class_id = self.id(0x7e577e57)
		load.class_name = 'java/util/List'
		self.hf.classloads_by_id[load.class_id] = load
		load = hprof._parsing.ClassLoad()
		load.class_id = self.id(0x7e577e56)
		load.class_name = 'java/util/LinkedList'
		self.hf.classloads_by_id[load.class_id] = load
		load = hprof._parsing.ClassLoad()
		load.class_id = self.id(0x7e577e55)
		load.class_name = 'java/util/ChainedList' # which is totally a real thing.
		self.hf.classloads_by_id[load.class_id] = load

		List = object()
		LinkedList = object()
		ChainedList = object()
		retvals = {
			'java/util/List': ('java.util.List', List),
			'java/util/LinkedList': ('java.util.LinkedList', LinkedList),
			'java/util/ChainedList': ('java.util.ChainedList', ChainedList),
		}

		with patch('hprof.heap._create_class', side_effect=lambda ct, n, s, sa, ian, iat: retvals[n]) as mock:
			data = (self.build()
					.id(0x7e577e55) # class object id
					.u4(0x124)      # stacktrace serial
					.id(0x7e577e56) # superclass id
					.id(0x10ade2)   # loader id
					.id(0x5151515)  # signer id
					.id(0x5ec002e)  # protection domain id
					.id(0x999999)   # reserved 1
					.id(0xaaaaaa)   # reserved 2
					.u4(0x40)       # instance size
					.u2(0x0)        # constant pool size
					.u2(0x0)        # static field count
					.u2(0x0)        # instance field count
			)
			self.doit(0x20, data)
			self.assertEqual(mock.call_count, 0)

			data = (self.build()
					.id(0x7e577e56) # class object id
					.u4(0x124)      # stacktrace serial
					.id(0x7e577e57) # superclass id
					.id(0x10ade2)   # loader id
					.id(0x5151515)  # signer id
					.id(0x5ec002e)  # protection domain id
					.id(0x999999)   # reserved 1
					.id(0xaaaaaa)   # reserved 2
					.u4(0x40)       # instance size
					.u2(0x0)        # constant pool size
					.u2(0x0)        # static field count
					.u2(0x0)        # instance field count
			)
			self.doit(0x20, data)
			self.assertEqual(mock.call_count, 0)

			data = (self.build()
					.id(0x7e577e57) # class object id
					.u4(0x124)      # stacktrace serial
					.id(0)          # superclass id
					.id(0x10ade2)   # loader id
					.id(0x5151515)  # signer id
					.id(0x5ec002e)  # protection domain id
					.id(0x999999)   # reserved 1
					.id(0xaaaaaa)   # reserved 2
					.u4(0x40)       # instance size
					.u2(0x0)        # constant pool size
					.u2(0x0)        # static field count
					.u2(0x0)        # instance field count
			)
			self.doit(0x20, data)
			self.assertEqual(mock.call_count, 3)

			self.assertEqual(len(mock.call_args_list[0][0]), 6)
			self.assertIs(   mock.call_args_list[0][0][0], self.heap.classtree)
			self.assertEqual(mock.call_args_list[0][0][1], 'java/util/List')
			self.assertIs(   mock.call_args_list[0][0][2], None)
			self.assertEqual(mock.call_args_list[0][0][3], {})
			self.assertEqual(mock.call_args_list[0][0][4], ())
			self.assertEqual(mock.call_args_list[2][0][5], ())
			self.assertEqual(mock.call_args_list[0][1], {})
			self.assertEqual(self.heap.classes.get('java.util.List'), [List])
			self.assertEqual(self.heap.get(self.id(0x7e577e57)), List)

			self.assertEqual(len(mock.call_args_list[1][0]), 6)
			self.assertIs(   mock.call_args_list[1][0][0], self.heap.classtree)
			self.assertEqual(mock.call_args_list[1][0][1], 'java/util/LinkedList')
			self.assertIs(   mock.call_args_list[1][0][2], List)
			self.assertEqual(mock.call_args_list[1][0][3], {})
			self.assertEqual(mock.call_args_list[1][0][4], ())
			self.assertEqual(mock.call_args_list[2][0][5], ())
			self.assertEqual(mock.call_args_list[1][1], {})
			self.assertEqual(self.heap.classes.get('java.util.LinkedList'), [LinkedList])
			self.assertEqual(self.heap.get(self.id(0x7e577e56)), LinkedList)

			self.assertEqual(len(mock.call_args_list[2][0]), 6)
			self.assertIs(   mock.call_args_list[2][0][0], self.heap.classtree)
			self.assertEqual(mock.call_args_list[2][0][1], 'java/util/ChainedList')
			self.assertIs(   mock.call_args_list[2][0][2], LinkedList)
			self.assertEqual(mock.call_args_list[2][0][3], {})
			self.assertEqual(mock.call_args_list[2][0][4], ())
			self.assertEqual(mock.call_args_list[2][0][5], ())
			self.assertEqual(mock.call_args_list[2][1], {})
			self.assertEqual(self.heap.classes.get('java.util.ChainedList'), [ChainedList])
			self.assertEqual(self.heap.get(self.id(0x7e577e55)), ChainedList)

			self.assertEqual(self.heap._deferred_classes, {})

			self.assertEqual(self.heap._instances[List], [])
			self.assertEqual(self.heap._instances[LinkedList], [])
			self.assertEqual(self.heap._instances[ChainedList], [])

	def test_super_not_found(self):
		load = hprof._parsing.ClassLoad()
		load.class_id = self.id(0x7e577e56)
		load.class_name = 'java/util/LinkedList'
		self.hf.classloads_by_id[load.class_id] = load
		load = hprof._parsing.ClassLoad()
		load.class_id = self.id(0x7e577e55)
		load.class_name = 'java/util/ChainedList' # which is totally a real thing.
		self.hf.classloads_by_id[load.class_id] = load
		load = hprof._parsing.ClassLoad()
		load.class_id = self.id(0x7e577e54)
		load.class_name = 'java/util/ArrayList'
		self.hf.classloads_by_id[load.class_id] = load

		with patch('hprof.heap._create_class') as mock:
			data = (self.build()
					.id(0x7e577e54) # class object id
					.u4(0x124)      # stacktrace serial
					.id(0x7e577e57) # superclass id
					.id(0x10ade2)   # loader id
					.id(0x5151515)  # signer id
					.id(0x5ec002e)  # protection domain id
					.id(0x999999)   # reserved 1
					.id(0xaaaaaa)   # reserved 2
					.u4(0x40)       # instance size
					.u2(0x0)        # constant pool size
					.u2(0x0)        # static field count
					.u2(0x0)        # instance field count
			)
			self.doit(0x20, data)
			self.assertEqual(mock.call_count, 0)

			data = (self.build()
					.id(0x7e577e55) # class object id
					.u4(0x124)      # stacktrace serial
					.id(0x7e577e56) # superclass id
					.id(0x10ade2)   # loader id
					.id(0x5151515)  # signer id
					.id(0x5ec002e)  # protection domain id
					.id(0x999999)   # reserved 1
					.id(0xaaaaaa)   # reserved 2
					.u4(0x40)       # instance size
					.u2(0x0)        # constant pool size
					.u2(0x0)        # static field count
					.u2(0x0)        # instance field count
			)
			self.doit(0x20, data)
			self.assertEqual(mock.call_count, 0)

			data = (self.build()
					.id(0x7e577e56) # class object id
					.u4(0x124)      # stacktrace serial
					.id(0x7e577e57) # superclass id
					.id(0x10ade2)   # loader id
					.id(0x5151515)  # signer id
					.id(0x5ec002e)  # protection domain id
					.id(0x999999)   # reserved 1
					.id(0xaaaaaa)   # reserved 2
					.u4(0x40)       # instance size
					.u2(0x0)        # constant pool size
					.u2(0x0)        # static field count
					.u2(0x0)        # instance field count
			)
			self.doit(0x20, data)
			self.assertEqual(mock.call_count, 0)

			with self.assertRaisesRegex(hprof.error.FormatError, 'super class'):
				hprof._parsing._instantiate(self.hf, self.idsize, None)
