# Copyright (C) 2019 Snild Dolkow
# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

import unittest
import hprof

class TestClassInstanceLookups(unittest.TestCase):

	def setUp(self):
		from hprof.heap import _create_class
		self.heap = hprof.heap.Heap()

		def c(name, supercls):
			name, cls = _create_class(self.heap.classtree, name, supercls, {}, (), ())
			self.heap._instances[cls] = []
			if name not in self.heap.classes:
				self.heap.classes[name] = []
			self.heap.classes[name].append(cls)
			return cls

		self.objectCls1 = c('java.lang.Object', None)
		self.objectCls2 = c('java.lang.Object', None)
		self.classCls   = c('java.lang.Class', self.objectCls1)
		self.listCls    = c('java.util.List', self.objectCls1)
		self.alistCls   = c('java.util.ArrayList', self.listCls)
		self.llistCls   = c('java.util.LinkedList', self.listCls)
		self.parrayCls  = c('[I', self.objectCls1)
		self.oarrayCls  = c('[Ljava.lang.Object;', self.objectCls1)
		self.larrayCls  = c('[Ljava.util.List;', self.oarrayCls)

		def mk(cls, *args):
			obj = cls(*args)
			self.heap._instances[cls].append(obj)
			return obj

		self.o1 = mk(self.objectCls1, 10)
		self.o2 = mk(self.objectCls1, 100)
		self.o3 = mk(self.objectCls1, 1000)
		self.p1 = mk(self.objectCls2, 200)
		self.p2 = mk(self.objectCls2, 2000)
		self.l1 = mk(self.listCls, 20)
		self.l2 = mk(self.listCls, 30)
		self.a1 = mk(self.alistCls, 40)
		self.a2 = mk(self.alistCls, 50)
		self.ia = mk(self.parrayCls, 7777, ())
		self.oa = mk(self.oarrayCls, 7778, ())
		self.la = mk(self.larrayCls, 7779, ())

	def test_objects(self):
		with self.subTest(scope='exact'):
			with self.subTest('cls1'):
				self.assertCountEqual(self.heap.exact_instances(self.objectCls1),
						(self.o1, self.o2, self.o3))
			with self.subTest('cls2'):
				self.assertCountEqual(self.heap.exact_instances(self.objectCls2),
						(self.p1, self.p2))
			with self.subTest('str'):
				self.assertCountEqual(self.heap.exact_instances('java.lang.Object'),
						(self.o1, self.o2, self.o3, self.p1, self.p2))
		with self.subTest(scope='all'):
			with self.subTest('cls1'):
				self.assertCountEqual(self.heap.all_instances(self.objectCls1),
						(self.o1, self.o2, self.o3, self.l1, self.l2,
						self.a1, self.a2, self.ia, self.oa, self.la,
						self.objectCls1, self.objectCls2, self.classCls,
						self.listCls, self.alistCls, self.llistCls,
						self.parrayCls, self.oarrayCls, self.larrayCls))
			with self.subTest('cls2'):
				self.assertCountEqual(self.heap.all_instances(self.objectCls2),
						(self.p1, self.p2))
			with self.subTest('str'):
				self.assertCountEqual(self.heap.all_instances('java.lang.Object'),
					(self.o1, self.o2, self.o3, self.l1, self.l2,
					self.a1, self.a2, self.ia, self.oa, self.la,
					self.p1, self.p2,
					self.objectCls1, self.objectCls2, self.classCls,
					self.listCls, self.alistCls, self.llistCls,
					self.parrayCls, self.oarrayCls, self.larrayCls))

	def test_classes(self):
		for key in (self.classCls, 'java.lang.Class'):
			with self.subTest(key=key):
				with self.subTest('exact'):
					self.assertCountEqual(self.heap.exact_instances(key),
							(self.objectCls1, self.objectCls2, self.classCls,
							self.listCls, self.alistCls, self.llistCls,
							self.parrayCls, self.oarrayCls, self.larrayCls))
				with self.subTest('all'):
					self.assertCountEqual(self.heap.all_instances(self.classCls),
							(self.objectCls1, self.objectCls2, self.classCls,
							self.listCls, self.alistCls, self.llistCls,
							self.parrayCls, self.oarrayCls, self.larrayCls))

	def test_lists(self):
		for key in (self.listCls, 'java.util.List'):
			with self.subTest(key=key):
				with self.subTest('exact'):
					self.assertCountEqual(self.heap.exact_instances(key),
							(self.l1, self.l2))
				with self.subTest('all'):
					self.assertCountEqual(self.heap.all_instances(key),
							(self.l1, self.l2, self.a1, self.a2))

	def test_arraylists(self):
		for key in (self.alistCls, 'java.util.ArrayList'):
			with self.subTest(key=key):
				with self.subTest('exact'):
					self.assertCountEqual(self.heap.exact_instances(key),
							(self.a1, self.a2))
				with self.subTest('all'):
					self.assertCountEqual(self.heap.all_instances(key),
							(self.a1, self.a2))

	def test_linkedlists(self):
		for key in (self.llistCls, 'java.util.LinkedList'):
			with self.subTest(key=key):
				with self.subTest('exact'):
					self.assertCountEqual(self.heap.exact_instances(key), ())
				with self.subTest('all'):
					self.assertCountEqual(self.heap.all_instances(key), ())

	def test_primarrays(self):
		for key in (self.parrayCls, 'int[]'):
			with self.subTest(key=key):
				with self.subTest('exact'):
					self.assertCountEqual(self.heap.exact_instances(key),
							(self.ia,))
				with self.subTest('all'):
					self.assertCountEqual(self.heap.all_instances(key),
							(self.ia,))

	def test_objarrays(self):
		for key in (self.oarrayCls, 'java.lang.Object[]'):
			with self.subTest(key=key):
				with self.subTest('exact'):
					self.assertCountEqual(self.heap.exact_instances(key),
							(self.oa,))
				with self.subTest('all'):
					self.assertCountEqual(self.heap.all_instances(key),
							(self.oa, self.la))

	def test_listarrays(self):
		for key in (self.larrayCls, 'java.util.List[]'):
			with self.subTest(key=key):
				with self.subTest('exact'):
					self.assertCountEqual(self.heap.exact_instances(key),
							(self.la,))
				with self.subTest('all'):
					self.assertCountEqual(self.heap.all_instances(key),
							(self.la,))
