from unittest import TestCase

import hprof

class TestJavaCarExample(TestCase):
	FILE = 'tests/java.hprof'

	@classmethod
	def setUpClass(self):
		self.hf = hprof.open(self.FILE)
		self.dump, = self.hf.dumps()
		self.main  = self.dump.get_class('Main')
		self.carex = self.dump.get_class('com.example.cars.CarExample')

	def test_find_class_by_name(self):
		self.assertIs(type(self.main),  hprof.heap.Class)
		self.assertIs(type(self.carex), hprof.heap.Class)
		self.assertEqual(self.main.hprof_name, 'Main')
		self.assertEqual(self.carex.hprof_name, 'com.example.cars.CarExample')

	def test_read_object_ref_to_class(self):
		bikeCls = self.carex.bikeSuper # whoops, 'bikeSuper' actually contains Bike, not Vehicle. :)
		self.assertIs(type(bikeCls), hprof.heap.Class)
		self.assertEqual(bikeCls, self.dump.get_class('com.example.cars.Bike'))

	def test_read_carex_superclasses(self):
		jobject = self.carex.hprof_super_class
		self.assertEqual(jobject, self.dump.get_class('java.lang.Object'))
		self.assertIsNone(jobject.hprof_super_class)

	def test_read_bike_superclasses(self):
		bike = self.dump.get_class('com.example.cars.Bike')
		vehicle = bike.hprof_super_class
		self.assertEqual(vehicle, self.dump.get_class('com.example.cars.Vehicle'))
		jobject = vehicle.hprof_super_class
		self.assertEqual(jobject, self.dump.get_class('java.lang.Object'))
		self.assertIsNone(jobject.hprof_super_class)

	def test_read_null_reference(self):
		self.assertIsNone(self.carex.nothing)

	def test_get_subclasses(self):
		objectcls = self.dump.get_class('java.lang.Object')
		vehiclecls = self.dump.get_class('com.example.cars.Vehicle')
		bikecls = self.dump.get_class('com.example.cars.Bike')
		limocls = self.dump.get_class('com.example.cars.Limo')
		carcls = self.dump.get_class('com.example.cars.Car')
		self.assertIn(vehiclecls, objectcls.hprof_subclasses())
		self.assertCountEqual(vehiclecls.hprof_subclasses(), (carcls, bikecls))
		self.assertCountEqual(bikecls.hprof_subclasses(), ())
		self.assertCountEqual(carcls.hprof_subclasses(), (limocls,))
		self.assertCountEqual(limocls.hprof_subclasses(), ())

	def test_find_instances_by_class(self):
		vehiclecls = self.dump.get_class('com.example.cars.Vehicle')
		instances = self.dump.find_instances(vehiclecls)

		carcls = self.dump.get_class('com.example.cars.Car')
		limocls = self.dump.get_class('com.example.cars.Limo')
		bikecls = self.dump.get_class('com.example.cars.Bike')
		for i in range(5):
			obj = next(instances)
			self.assertIs(type(obj), hprof.heap.Object)
			self.assertIn(obj.hprof_class, (carcls, bikecls, limocls))
		with self.assertRaises(StopIteration):
			next(instances)

	def test_find_instances_by_name(self):
		instances = self.dump.find_instances('com.example.cars.Vehicle')

		carcls = self.dump.get_class('com.example.cars.Car')
		limocls = self.dump.get_class('com.example.cars.Limo')
		bikecls = self.dump.get_class('com.example.cars.Bike')
		for i in range(5):
			obj = next(instances)
			self.assertIs(type(obj), hprof.heap.Object)
			self.assertIn(obj.hprof_class, (carcls, bikecls, limocls))
		with self.assertRaises(StopIteration):
			next(instances)

	def test_get_exact_instances_by_class(self):
		carcls = self.dump.get_class('com.example.cars.Car')
		instances = self.dump.find_instances(carcls, False)

		for i in range(2):
			obj = next(instances)
			self.assertIs(type(obj), hprof.heap.Object)
			self.assertEqual(obj.hprof_class, carcls)
		with self.assertRaises(StopIteration):
			next(instances)

	def test_get_exact_instances_by_name(self):
		carcls = self.dump.get_class('com.example.cars.Car')
		instances = self.dump.find_instances('com.example.cars.Car', False)

		for i in range(2):
			obj = next(instances)
			self.assertIs(type(obj), hprof.heap.Object)
			self.assertEqual(obj.hprof_class, carcls)
		with self.assertRaises(StopIteration):
			next(instances)
