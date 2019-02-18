#!/usr/bin/env python3
#coding=utf8

from unittest import TestCase

from hprof.immutable import Immutable

class Coord(Immutable):
	__slots__ = ('x', 'y')

	def __init__(self, x, y):
		self.x = x
		self.y = y

class SubCoord(Coord):
	__slots__ = 'z',

	def __init__(self, x, y, z):
		super().__init__(x, y)
		self.z = z

class NiceString(Immutable):
	def __str__(self):
		return 'nice'

class NiceInt(Immutable):
	__slots__ = 'val',

	def __init__(self, val):
		self.val = val

class Lazy(Immutable):
	__slots__ = 'val'

class Private(Immutable):
	__slots__ = 'pub', '_priv'

	def __init__(self, pub, priv):
		self.pub = pub
		self._priv = priv

class TestImmutable(TestCase):
	def setUp(self):
		self.c = Coord(5, 6)
		self.s = SubCoord(7, 8, 9)
		self.n = NiceString()
		self.i = NiceInt(33)
		self.z = Lazy()
		self.p = Private(1, 2)

	def test_immutable_subclass_set(self):
		with self.assertRaisesRegex(AttributeError, 'immutable'):
			self.c.x = 3
		with self.assertRaisesRegex(AttributeError, 'immutable'):
			self.c.y = 3

	def test_immutable_subsubclass_set(self):
		with self.assertRaisesRegex(AttributeError, 'immutable'):
			self.s.x = 3
		with self.assertRaisesRegex(AttributeError, 'immutable'):
			self.s.y = 3
		with self.assertRaisesRegex(AttributeError, 'immutable'):
			self.s.z = 3

	def test_immutable_subnothing_set(self):
		with self.assertRaisesRegex(AttributeError, 'immutable'):
			self.i.val = 10

	def test_immutable_lazy_set(self):
		self.z.val = 7
		with self.assertRaisesRegex(AttributeError, 'immutable'):
			self.z.val = 8

	def test_immutable_private_set(self):
		self.p._priv = 80
		with self.assertRaisesRegex(AttributeError, 'immutable'):
			self.p.pub = 70

	def test_immutable_subclass_add(self):
		with self.assertRaisesRegex(AttributeError, 'has no attribute'):
			self.c.z = 10

	def test_immutable_subsubclass_add(self):
		with self.assertRaisesRegex(AttributeError, 'has no attribute'):
			self.s.w = 10

	def test_immutable_nothing_add(self):
		with self.assertRaisesRegex(AttributeError, 'has no attribute'):
			self.n.val = 8

	def test_immutable_subnothing_add(self):
		with self.assertRaisesRegex(AttributeError, 'has no attribute'):
			self.i.y = 3

	def test_immutable_lazy_add(self):
		with self.assertRaisesRegex(AttributeError, 'has no attribute'):
			self.z.y = 4

	def test_immutable_private_add(self):
		with self.assertRaisesRegex(AttributeError, 'has no attribute'):
			self.p.protected = 10

	def test_immutable_cheat(self):
		object.__setattr__(self.c, 'x', 100)
		self.assertEqual(self.c.x, 100)
		with self.assertRaisesRegex(AttributeError, 'has no attribute'):
			object.__setattr__(self.c, 'z', 100)

	def test_immutable_multiple_inheritance(self):
		with self.assertRaisesRegex(TypeError, 'multiple inheritance'):
			type('TwoParent', (str, Immutable), {})
		with self.assertRaisesRegex(TypeError, 'multiple inheritance'):
			type('TwoParent', (Immutable, str), {})
