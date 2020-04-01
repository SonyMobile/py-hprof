# Copyright (C) 2019 Snild Dolkow
# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

class TestCars(object):
	def setUp(self):
		self.heap, = self.hf.heaps
		self.cars, = self.heap.exact_instances('com.example.Cars')
		self.stringCls, = self.heap.classes['java.lang.String']

	def test_find_instances(self):
		self.assertCountEqual(self.heap.all_instances('com.example.cars.Vehicle'),
				(self.cars.swe, self.cars.jap, self.cars.generic,
				self.cars.mine, self.cars.redYellow))
		self.assertCountEqual(self.heap.all_instances('com.example.cars.Car'),
				(self.cars.swe, self.cars.jap, self.cars.generic))
		self.assertCountEqual(self.heap.exact_instances('com.example.cars.Vehicle'), ())
		self.assertCountEqual(self.heap.exact_instances('com.example.cars.Car'),
				(self.cars.swe, self.cars.jap))

	def test_num_wheels(self):
		self.assertEqual(self.cars.swe.numWheels, 4)
		self.assertEqual(self.cars.jap.numWheels, 4)
		self.assertEqual(self.cars.generic.numWheels, 4)
		self.assertEqual(self.cars.mine.numWheels, 2)
		self.assertEqual(self.cars.redYellow.numWheels, 2)

	def test_vehicle_makes(self):
		# TODO: add special handling for String __eq__()
		# e.g. self.assertEqual(self.cars.swe.make, 'Lolvo')
		self.assertIsInstance(self.cars.swe.make, self.stringCls)
		self.assertIsInstance(self.cars.jap.make, self.stringCls)
		self.assertIsInstance(self.cars.generic.make, self.stringCls)
		self.assertIsInstance(self.cars.mine.make, self.stringCls)
		self.assertIsInstance(self.cars.redYellow.make, self.stringCls)

		# str() of String?
		self.assertEqual(str(self.cars.swe.make), 'Lolvo')
		self.assertEqual(str(self.cars.jap.make), 'Toy Yoda')
		self.assertEqual(str(self.cars.generic.make), 'Stretch')
		self.assertEqual(str(self.cars.mine.make), 'Fånark')
		self.assertEqual(str(self.cars.redYellow.make), 'Axes')

	def test_vehicle_array(self):
		self.assertEqual(len(self.cars.vehicles), 5)
		self.assertIs(self.cars.vehicles[0], self.cars.swe)
		self.assertIs(self.cars.vehicles[1], self.cars.jap)
		self.assertIs(self.cars.vehicles[2], self.cars.generic)
		self.assertIs(self.cars.vehicles[3], self.cars.mine)
		self.assertIs(self.cars.vehicles[4], self.cars.redYellow)

	def test_class_hierarchy(self):
		vehicle, = self.heap.classes['com.example.cars.Vehicle']
		car,     = self.heap.classes['com.example.cars.Car']
		limo,    = self.heap.classes['com.example.cars.Limo']
		bike,    = self.heap.classes['com.example.cars.Bike']
		self.assertTrue( issubclass(vehicle, vehicle))
		self.assertTrue( issubclass(    car, vehicle))
		self.assertTrue( issubclass(   limo, vehicle))
		self.assertTrue( issubclass(   bike, vehicle))
		self.assertFalse(issubclass(vehicle, car))
		self.assertTrue( issubclass(    car, car))
		self.assertTrue( issubclass(   limo, car))
		self.assertFalse(issubclass(   bike, car))
		self.assertFalse(issubclass(vehicle, limo))
		self.assertFalse(issubclass(    car, limo))
		self.assertTrue( issubclass(   limo, limo))
		self.assertFalse(issubclass(   bike, limo))
		self.assertFalse(issubclass(vehicle, bike))
		self.assertFalse(issubclass(    car, bike))
		self.assertFalse(issubclass(   limo, bike))
		self.assertTrue( issubclass(   bike, bike))

	def test_isinstance(self):
		vehicle, = self.heap.classes['com.example.cars.Vehicle']
		car,     = self.heap.classes['com.example.cars.Car']
		limo,    = self.heap.classes['com.example.cars.Limo']
		bike,    = self.heap.classes['com.example.cars.Bike']
		self.assertIsInstance(   self.cars.swe,       vehicle)
		self.assertIsInstance(   self.cars.jap,       vehicle)
		self.assertIsInstance(   self.cars.generic,   vehicle)
		self.assertIsInstance(   self.cars.mine,      vehicle)
		self.assertIsInstance(   self.cars.redYellow, vehicle)
		self.assertIsInstance(   self.cars.swe,       car)
		self.assertIsInstance(   self.cars.jap,       car)
		self.assertIsInstance(   self.cars.generic,   car)
		self.assertNotIsInstance(self.cars.mine,      car)
		self.assertNotIsInstance(self.cars.redYellow, car)
		self.assertNotIsInstance(self.cars.swe,       limo)
		self.assertNotIsInstance(self.cars.jap,       limo)
		self.assertIsInstance(   self.cars.generic,   limo)
		self.assertNotIsInstance(self.cars.mine,      limo)
		self.assertNotIsInstance(self.cars.redYellow, limo)
		self.assertNotIsInstance(self.cars.swe,       bike)
		self.assertNotIsInstance(self.cars.jap,       bike)
		self.assertNotIsInstance(self.cars.generic,   bike)
		self.assertIsInstance(   self.cars.mine,      bike)
		self.assertIsInstance(   self.cars.redYellow, bike)

