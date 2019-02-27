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
