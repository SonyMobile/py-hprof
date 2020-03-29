# Copyright (C) 2019 Snild Dolkow
# Licensed under the LICENSE.

class TestArrays(object):
	def setUp(self):
		heap, = self.hf.heaps
		self.iaCls,  = heap.classes['int[]']
		self.iaaCls, = heap.classes['int[][]']
		self.caCls,  = heap.classes['char[]']
		self.caaCls, = heap.classes['char[][]']
		self.a, = heap.exact_instances('com.example.Arrays')

	def test_int_array(self):
		self.assertIsInstance(self.a.i1, self.iaCls)
		self.assertEqual(len(self.a.i1), 3)
		self.assertEqual(self.a.i1[0], 1)
		self.assertEqual(self.a.i1[1], 2)
		self.assertEqual(self.a.i1[2], 3)

	def test_int_matrix(self):
		self.assertIsInstance(self.a.i2, self.iaaCls)
		self.assertEqual(len(self.a.i2), 2)
		self.assertEqual(self.a.i2[0][0], 10)
		self.assertEqual(self.a.i2[0][1], 15)
		self.assertEqual(self.a.i2[1][0], 13)
		self.assertEqual(self.a.i2[1][1], 11)

	def test_char_array(self):
		self.assertIsInstance(self.a.c1, self.caCls)
		self.assertEqual(len(self.a.c1), 5)
		self.assertEqual(self.a.c1[0], 'h')
		self.assertEqual(self.a.c1[1], 'e')
		self.assertEqual(self.a.c1[2], 'l')
		self.assertEqual(self.a.c1[3], 'l')
		self.assertEqual(self.a.c1[4], 'o')

	def test_char_matrix(self):
		self.assertIsInstance(self.a.c2, self.caaCls)
		self.assertEqual(len(self.a.c2), 2)
		self.assertIs(self.a.c2[0], self.a.c1)
		self.assertIsInstance(self.a.c2[1], self.caCls)
		self.assertEqual(len(self.a.c2[1]), 5)
		self.assertEqual(self.a.c2[1][0], 'w')
		self.assertEqual(self.a.c2[1][1], 'o')
		self.assertEqual(self.a.c2[1][2], 'r')
		self.assertEqual(self.a.c2[1][3], 'l')
		self.assertEqual(self.a.c2[1][4], 'd')
