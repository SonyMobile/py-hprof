import unittest

# This file is essentially a test/demo of *python* behavior that the
# hprof library will (_probably_, as of this writing) depend on.
# Here be metadragons.

class Vehicle(object):
	__slots__ = ('wheels', 'speed')
	def __init__(self):
		Vehicle.wheels.__set__(self, 10)
		self.wheels = 78
		self.speed  = 1

class Car(Vehicle):
	__slots__ = ('wheels', 'doors') # note the repeated 'wheels' attr
	def __init__(self):
		super().__init__()
		self.wheels = 4
		self.speed  = 100
		self.doors = 5

class House(object):
	__slots__ = ('doors', 'size', 'wheels')
	def __init__(self):
		self.doors = 2
		self.size = 200
		self.wheels = 0


class TestAccesses(unittest.TestCase):
	def test_obvious_stuff(self):
		# just to warm you up. :)
		c = Car()
		v = Vehicle()
		h = House()
		self.assertEqual(c.doors, 5)
		self.assertEqual(c.speed, 100)
		self.assertEqual(v.speed, 1)
		self.assertEqual(c.wheels, 4)
		self.assertEqual(v.wheels, 78)
		self.assertEqual(h.doors, 2)
		self.assertEqual(h.size, 200)
		self.assertEqual(h.wheels, 0)

	def test_descriptor_access_car(self):
		c = Car()
		self.assertEqual(Vehicle.wheels.__get__(c), 10)
		self.assertEqual(Car    .wheels.__get__(c),  4)
		self.assertEqual(Vehicle.speed.__get__(c), 100)
		self.assertEqual(Car    .speed.__get__(c), 100) # oh python, you make me so happy!
		self.assertEqual(Car    .doors.__get__(c),   5)
		with self.assertRaises(TypeError):
			House.wheels.__get__(c)

	def test_descriptor_access_vehicle(self):
		v = Vehicle()
		self.assertEqual(Vehicle.wheels.__get__(v), 78) # there's that 78!
		self.assertEqual(Vehicle.speed.__get__(v), 1)
		with self.assertRaises(TypeError):
			House.wheels.__get__(v)

	def test_dynamic_descriptor_access(self):
		c = Car()
		self.assertEqual(getattr(Car, 'wheels').__get__(c), 4)
		self.assertEqual(getattr(Vehicle, 'wheels').__get__(c), 10)
