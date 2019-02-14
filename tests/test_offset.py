#!/usr/bin/env python3
#coding=utf8

from datetime import datetime, timedelta
from unittest import TestCase

from hprof.offset import *

class TestOffset(TestCase):
	def test_offset_flatten(self):
		self.assertEqual(offset( 5, 7).flatten(4),  33)
		self.assertEqual(offset( 2, 2).flatten(2),   6)
		self.assertEqual(offset(19, 0).flatten(3),  19)
		self.assertEqual(offset(-2,-5).flatten(8), -42)
		self.assertEqual(offset(10,11).flatten(4),  54)
		self.assertEqual(offset(10,11).flatten(8),  98)

	def test_offset_equal(self):
		a = offset(17,5)
		b = offset(17,5)
		c = offset(16,5)
		d = offset(17,6)
		self.assertEqual(   a, a)
		self.assertEqual(   a, b)
		self.assertNotEqual(a, c)
		self.assertNotEqual(a, d)
		self.assertEqual(   b, a)
		self.assertEqual(   b, b)
		self.assertNotEqual(b, c)
		self.assertNotEqual(b, d)
		self.assertNotEqual(c, a)
		self.assertNotEqual(c, b)
		self.assertEqual(   c, c)
		self.assertNotEqual(c, d)
		self.assertNotEqual(d, a)
		self.assertNotEqual(d, b)
		self.assertNotEqual(d, c)
		self.assertEqual(   d, d)
		for x in range(100):
			for o in (a, b, c, d):
				self.assertNotEqual(o, x)
				self.assertNotEqual(x, o)
				self.assertNotEqual(o, str(x))
				self.assertNotEqual(str(x), o)

	def test_offset_plus_zero(self):
		orig = offset(7,17)
		self.assertEqual(orig, orig + 0)
		self.assertEqual(orig, 0 + orig)

	def test_offset_plus_one(self):
		orig = offset(9,16)
		self.assertEqual(orig + 1, offset(10, 16))
		self.assertEqual(1 + orig, offset(10, 16))

	def test_offset_plus_bytes(self):
		self.assertEqual(byteoffset(7) + idoffset(3), offset(7, 3))
		self.assertEqual(byteoffset(9) + idoffset(3), offset(9, 3))
		self.assertEqual(byteoffset(9) + idoffset(1), offset(9, 1))
		self.assertEqual(idoffset(3) + byteoffset(7), offset(7, 3))
		self.assertEqual(idoffset(3) + byteoffset(9), offset(9, 3))
		self.assertEqual(idoffset(1) + byteoffset(9), offset(9, 1))

	def test_offset_unary_minus(self):
		self.assertEqual(offset(-3,-5), -offset(3,5))
		self.assertEqual(offset(7,11), -offset(-7,-11))

	def test_offset_minus_zero(self):
		self.assertEqual(offset(7, 10) - 0, offset(7, 10))
		self.assertEqual(0 - offset(7, 10), offset(-7, -10))

	def test_offset_minus_one(self):
		self.assertEqual(offset(7, 10) - 1, offset(6, 10))
		self.assertEqual(1 - offset(7, 10), offset(-6, -10))

	def test_offset_minus_bytes(self):
		self.assertEqual(byteoffset(3) - idoffset(5), offset(3, -5))
		self.assertEqual(idoffset(3) - byteoffset(5), offset(-5, 3))

	def test_idoffset(self):
		self.assertEqual(idoffset(3), offset(0, 3))
		self.assertEqual(idoffset(70), offset(0, 70))

	def test_byteoffset(self):
		self.assertEqual(byteoffset(3), offset(3, 0))
		self.assertEqual(byteoffset(70), offset(70, 0))

	def test_add_offset(self):
		a = offset(3,5)
		b = offset(11,13)
		self.assertEqual(a + b, offset(14, 18))
		self.assertEqual(b + a, offset(14, 18))

	def test_add_string(self):
		with self.assertRaises(TypeError):
			offset(3,7) + 'hello'

	def test_offset_not_comparable(self):
		a = offset(2,3)
		b = offset(5,7)
		with self.assertRaises(TypeError):
			a < b
		with self.assertRaises(TypeError):
			a > b
		with self.assertRaises(TypeError):
			a <= b
		with self.assertRaises(TypeError):
			a >= b
		with self.assertRaises(TypeError):
			b < a
		with self.assertRaises(TypeError):
			b > a
		with self.assertRaises(TypeError):
			b <= a
		with self.assertRaises(TypeError):
			b >= a
