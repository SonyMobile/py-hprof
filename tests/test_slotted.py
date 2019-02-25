from unittest import TestCase

from hprof._slotted import Slotted

class Coord(object, metaclass=Slotted):
	__slots__ = ('x', 'y')

	def __init__(self, x, y):
		self.x = x
		self.y = y

class SubCoord(Coord):
	__slots__ = 'z',

	def __init__(self, x, y, z):
		super().__init__(x, y)
		self.z = z

class NiceString(object, metaclass=Slotted):
	def __str__(self):
		return 'nice'

class NiceInt(object, metaclass=Slotted):
	__slots__ = 'val',

	def __init__(self, val):
		self.val = val

class Lazy(object, metaclass=Slotted):
	__slots__ = 'val'

class Private(object, metaclass=Slotted):
	__slots__ = 'pub', '_priv'

	def __init__(self, pub, priv):
		self.pub = pub
		self._priv = priv

class TestSlotted(TestCase):
	def setUp(self):
		self.c = Coord(5, 6)
		self.s = SubCoord(7, 8, 9)
		self.n = NiceString()
		self.i = NiceInt(33)
		self.z = Lazy()
		self.p = Private(1, 2)

	def test_slotted_subclass_add(self):
		with self.assertRaisesRegex(AttributeError, 'has no attribute'):
			self.c.z = 10

	def test_slotted_subsubclass_add(self):
		with self.assertRaisesRegex(AttributeError, 'has no attribute'):
			self.s.w = 10

	def test_slotted_nothing_add(self):
		with self.assertRaisesRegex(AttributeError, 'has no attribute'):
			self.n.val = 8

	def test_slotted_subnothing_add(self):
		with self.assertRaisesRegex(AttributeError, 'has no attribute'):
			self.i.y = 3

	def test_slotted_lazy_add(self):
		with self.assertRaisesRegex(AttributeError, 'has no attribute'):
			self.z.y = 4

	def test_slotted_private_add(self):
		with self.assertRaisesRegex(AttributeError, 'has no attribute'):
			self.p.protected = 10

	def test_slotted_cheat(self):
		object.__setattr__(self.c, 'x', 100)
		self.assertEqual(self.c.x, 100)
		with self.assertRaisesRegex(AttributeError, 'has no attribute'):
			object.__setattr__(self.c, 'z', 100)

	def test_slotted_multiple_inheritance(self):
		with self.assertRaisesRegex(TypeError, 'multiple inheritance'):
			type('TwoParent', (Lazy, Coord), {})
		with self.assertRaisesRegex(TypeError, 'multiple inheritance'):
			type('TwoParent', (Coord, Lazy), {})

	def test_slotted_nonslotted_inheritance(self):
		with self.assertRaisesRegex(TypeError, 'superclass.*Slotted'):
			Slotted('BadParent', (str,), {})
