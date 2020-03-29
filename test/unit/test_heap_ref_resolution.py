# Copyright (C) 2019 Snild Dolkow
# Licensed under the LICENSE.

import hprof
import unittest

from unittest.mock import MagicMock

resolve = hprof._heap_parsing.resolve_heap_references

class TestHeapRefResolution(unittest.TestCase):

	def setUp(self):
		self.heap = hprof.heap.Heap()
		_, self.ObjectCls = hprof.heap._create_class(
				self.heap.classtree, 'java/lang/Object', None,
				{
					'cl': 8010,
					'co': hprof._heap_parsing.DeferredRef(0xf00d),
					'ci': 7,
					'cp': hprof._heap_parsing.DeferredRef(0xfade),
				},
				{
					'il': hprof.jtype.long,
					'io': hprof.jtype.object,
					'ii': hprof.jtype.int,
					'ip': hprof.jtype.object,
				},
		)
		_, self.ObjectArrayCls = hprof.heap._create_class(
				self.heap.classtree, '[Ljava/lang/Object;', self.ObjectCls, {}, {}
		)
		_, self.StringCls = hprof.heap._create_class(
				self.heap.classtree, 'java/lang/String', self.ObjectCls,
				{
					'dummy': hprof._heap_parsing.DeferredRef(0xdead),
				},
				{
					'iattr': hprof.jtype.object,
				},
		)
		_, self.IntArrayCls = hprof.heap._create_class(
				self.heap.classtree, '[I', self.ObjectCls, {}, {}
		)

		self.heap[0x0c]  = self.ObjectCls
		self.heap[0x0ac] = self.ObjectArrayCls
		self.heap[0x5c]  = self.StringCls
		self.heap[0x1ac] = self.IntArrayCls

		self.heap.classes['java.lang.Object']   = [self.ObjectCls]
		self.heap.classes['java.lang.Object[]'] = [self.ObjectArrayCls]
		self.heap.classes['java.lang.String[]'] = [self.StringCls]
		self.heap.classes['int[]']              = [self.IntArrayCls]

		self.f00d = self.heap[0xf00d] = self.StringCls(0xf00d)
		self.ObjectCls._hprof_ifieldvals.__set__(self.f00d, (10, 0xfade, 20, 0xf00d))
		self.StringCls._hprof_ifieldvals.__set__(self.f00d, (0xdead,))

		self.fade = self.heap[0xfade] = self.ObjectCls(0xfade)
		self.ObjectCls._hprof_ifieldvals.__set__(self.fade, (1, 0xdead, 2, 0xdead))

		self.dead = self.heap[0xdead] = self.StringCls(0xdead)
		self.ObjectCls._hprof_ifieldvals.__set__(self.dead, (11, 0x0000, 20, 0xfade))
		self.StringCls._hprof_ifieldvals.__set__(self.dead, (0xbeef,))

		self.beef = self.heap[0xbeef] = self.ObjectArrayCls(0xbeef)
		self.beef._hprof_array_data = (0xf00d, 0xdead, 0xfade, 0xf00d, 0xfade)

		self.ints = self.heap[0x1111] = self.IntArrayCls(0x1111)
		self.ints._hprof_array_data = hprof.heap._DeferredArrayData(hprof.jtype.int, b'abcdefgh')

	def test_objarray_resolution(self):
		resolve(self.heap, None)
		self.assertEqual(len(self.beef), 5)
		self.assertIs(self.beef[0], self.f00d)
		self.assertIs(self.beef[1], self.dead)
		self.assertIs(self.beef[2], self.fade)
		self.assertIs(self.beef[3], self.f00d)
		self.assertIs(self.beef[4], self.fade)

	def test_primarray_no_resolution(self):
		resolve(self.heap, None)
		self.assertEqual(len(self.ints), 2)
		self.assertEqual(self.ints[0], 0x61626364)
		self.assertEqual(self.ints[1], 0x65666768)

	def test_obj_instance_resolution(self):
		resolve(self.heap, None)
		self.assertEqual(self.fade.il, 1)
		self.assertIs(self.fade.io, self.dead)
		self.assertEqual(self.fade.ii, 2)
		self.assertIs(self.fade.ip, self.dead)
		self.assertEqual(self.fade.cl, 8010)
		self.assertIs(self.fade.co, self.f00d)
		self.assertEqual(self.fade.ci, 7)
		self.assertIs(self.fade.cp, self.fade)

	def test_obj_class_resolution(self):
		resolve(self.heap, None)
		self.assertEqual(self.ObjectCls.cl, 8010)
		self.assertIs(self.ObjectCls.co, self.f00d)
		self.assertEqual(self.ObjectCls.ci, 7)
		self.assertIs(self.ObjectCls.cp, self.fade)

	def test_string_instance_resolution(self):
		resolve(self.heap, None)
		with self.subTest('0xf00d'):
			self.assertEqual(self.f00d.il, 10)
			self.assertIs(self.f00d.io, self.fade)
			self.assertEqual(self.f00d.ii, 20)
			self.assertIs(self.f00d.ip, self.f00d)
			self.assertIs(self.f00d.iattr, self.dead)
			self.assertEqual(self.f00d.cl, 8010)
			self.assertIs(self.f00d.co, self.f00d)
			self.assertEqual(self.f00d.ci, 7)
			self.assertIs(self.f00d.cp, self.fade)
		with self.subTest('0xdead'):
			self.assertEqual(self.dead.il, 11)
			self.assertIsNone(self.dead.io)
			self.assertEqual(self.dead.ii, 20)
			self.assertIs(self.dead.ip, self.fade)
			self.assertIs(self.dead.iattr, self.beef)
			self.assertEqual(self.dead.cl, 8010)
			self.assertIs(self.dead.co, self.f00d)
			self.assertEqual(self.dead.ci, 7)
			self.assertIs(self.dead.cp, self.fade)

	def test_string_class_resolution(self):
		resolve(self.heap, None)
		self.assertEqual(self.StringCls.cl, 8010)
		self.assertIs(self.StringCls.co, self.f00d)
		self.assertEqual(self.StringCls.ci, 7)
		self.assertIs(self.StringCls.cp, self.fade)
		self.assertIs(self.StringCls.dummy, self.dead)

	def test_dangling_ref_iattr(self):
		self.StringCls._hprof_ifieldvals.__set__(self.dead, (0xbadf00d,))
		with self.assertRaisesRegex(hprof.error.MissingObject, '0xbadf00d'):
			resolve(self.heap, None)

	def test_dangling_ref_sattr(self):
		self.ObjectCls._hprof_sfields['co'] = hprof._heap_parsing.DeferredRef(0xdeadbeef)
		with self.assertRaisesRegex(hprof.error.MissingObject, '0xdeadbeef'):
			resolve(self.heap, None)

	def test_dangling_ref_array(self):
		self.beef._hprof_array_data = (0xf00d, 0xdead, 0xca7f00d, 0xf00d, 0xfade)
		with self.assertRaisesRegex(hprof.error.MissingObject, '0xca7f00d'):
			resolve(self.heap, None)

	def test_progress_callback(self):
		cb = MagicMock()
		resolve(self.heap, cb)
		self.assertEqual(cb.call_count, 2)
		self.assertEqual(cb.call_args_list[0][0], (0,))
		self.assertEqual(cb.call_args_list[1][0], (9,))

	def test_progress_callback_no_objs(self):
		heap = hprof.heap.Heap()
		cb = MagicMock()
		resolve(heap, cb)
		self.assertEqual(cb.call_count, 2)
		self.assertEqual(cb.call_args_list[0][0], (0,))
		self.assertEqual(cb.call_args_list[1][0], (0,))

	def test_progress_callback_many_objs(self):
		heap = MagicMock()
		heap._deferred_classes = []
		heap.values.return_value = (self.ObjectCls for i in range(10009))
		heap.__len__.return_value = 10009
		cb = MagicMock()
		resolve(heap, cb)
		self.assertEqual(cb.call_count, 3)
		self.assertEqual(cb.call_args_list[0][0], (0,))
		self.assertEqual(cb.call_args_list[1][0], (10000,))
		self.assertEqual(cb.call_args_list[2][0], (10009,))
