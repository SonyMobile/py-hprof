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

	def test_is_descendant(self):
		classcls = self.dump.get_class('java.lang.Class')
		maincls = self.dump.get_class('Main')
		objectcls = self.dump.get_class('java.lang.Object')
		vehiclecls = self.dump.get_class('com.example.cars.Vehicle')
		carcls = self.dump.get_class('com.example.cars.Car')
		bikecls = self.dump.get_class('com.example.cars.Bike')
		limocls = self.dump.get_class('com.example.cars.Limo')

		self.assertTrue( classcls.hprof_descendantof(classcls))
		self.assertFalse(classcls.hprof_descendantof(maincls))
		self.assertTrue( classcls.hprof_descendantof(objectcls))
		self.assertFalse(classcls.hprof_descendantof(vehiclecls))
		self.assertFalse(classcls.hprof_descendantof(carcls))
		self.assertFalse(classcls.hprof_descendantof(bikecls))
		self.assertFalse(classcls.hprof_descendantof(limocls))

		self.assertFalse(maincls.hprof_descendantof(classcls))
		self.assertTrue( maincls.hprof_descendantof(maincls))
		self.assertTrue( maincls.hprof_descendantof(objectcls))
		self.assertFalse(maincls.hprof_descendantof(vehiclecls))
		self.assertFalse(maincls.hprof_descendantof(carcls))
		self.assertFalse(maincls.hprof_descendantof(bikecls))
		self.assertFalse(maincls.hprof_descendantof(limocls))

		self.assertFalse(objectcls.hprof_descendantof(classcls))
		self.assertFalse(objectcls.hprof_descendantof(maincls))
		self.assertTrue( objectcls.hprof_descendantof(objectcls))
		self.assertFalse(objectcls.hprof_descendantof(vehiclecls))
		self.assertFalse(objectcls.hprof_descendantof(carcls))
		self.assertFalse(objectcls.hprof_descendantof(bikecls))
		self.assertFalse(objectcls.hprof_descendantof(limocls))

		self.assertFalse(vehiclecls.hprof_descendantof(classcls))
		self.assertFalse(vehiclecls.hprof_descendantof(maincls))
		self.assertTrue( vehiclecls.hprof_descendantof(objectcls))
		self.assertTrue( vehiclecls.hprof_descendantof(vehiclecls))
		self.assertFalse(vehiclecls.hprof_descendantof(carcls))
		self.assertFalse(vehiclecls.hprof_descendantof(bikecls))
		self.assertFalse(vehiclecls.hprof_descendantof(limocls))

		self.assertFalse(carcls.hprof_descendantof(classcls))
		self.assertFalse(carcls.hprof_descendantof(maincls))
		self.assertTrue( carcls.hprof_descendantof(objectcls))
		self.assertTrue( carcls.hprof_descendantof(vehiclecls))
		self.assertTrue( carcls.hprof_descendantof(carcls))
		self.assertFalse(carcls.hprof_descendantof(bikecls))
		self.assertFalse(carcls.hprof_descendantof(limocls))

		self.assertFalse(bikecls.hprof_descendantof(classcls))
		self.assertFalse(bikecls.hprof_descendantof(maincls))
		self.assertTrue( bikecls.hprof_descendantof(objectcls))
		self.assertTrue( bikecls.hprof_descendantof(vehiclecls))
		self.assertFalse(bikecls.hprof_descendantof(carcls))
		self.assertTrue( bikecls.hprof_descendantof(bikecls))
		self.assertFalse(bikecls.hprof_descendantof(limocls))

		self.assertFalse(limocls.hprof_descendantof(classcls))
		self.assertFalse(limocls.hprof_descendantof(maincls))
		self.assertTrue( limocls.hprof_descendantof(objectcls))
		self.assertTrue( limocls.hprof_descendantof(vehiclecls))
		self.assertTrue( limocls.hprof_descendantof(carcls))
		self.assertFalse(limocls.hprof_descendantof(bikecls))
		self.assertTrue( limocls.hprof_descendantof(limocls))

	def test_is_ancestor(self):
		classcls = self.dump.get_class('java.lang.Class')
		maincls = self.dump.get_class('Main')
		objectcls = self.dump.get_class('java.lang.Object')
		vehiclecls = self.dump.get_class('com.example.cars.Vehicle')
		carcls = self.dump.get_class('com.example.cars.Car')
		bikecls = self.dump.get_class('com.example.cars.Bike')
		limocls = self.dump.get_class('com.example.cars.Limo')

		self.assertTrue( classcls.hprof_ancestorof(classcls))
		self.assertFalse(classcls.hprof_ancestorof(maincls))
		self.assertFalse(classcls.hprof_ancestorof(objectcls))
		self.assertFalse(classcls.hprof_ancestorof(vehiclecls))
		self.assertFalse(classcls.hprof_ancestorof(carcls))
		self.assertFalse(classcls.hprof_ancestorof(bikecls))
		self.assertFalse(classcls.hprof_ancestorof(limocls))

		self.assertFalse(maincls.hprof_ancestorof(classcls))
		self.assertTrue( maincls.hprof_ancestorof(maincls))
		self.assertFalse(maincls.hprof_ancestorof(objectcls))
		self.assertFalse(maincls.hprof_ancestorof(vehiclecls))
		self.assertFalse(maincls.hprof_ancestorof(carcls))
		self.assertFalse(maincls.hprof_ancestorof(bikecls))
		self.assertFalse(maincls.hprof_ancestorof(limocls))

		self.assertTrue(objectcls.hprof_ancestorof(classcls))
		self.assertTrue(objectcls.hprof_ancestorof(maincls))
		self.assertTrue(objectcls.hprof_ancestorof(objectcls))
		self.assertTrue(objectcls.hprof_ancestorof(vehiclecls))
		self.assertTrue(objectcls.hprof_ancestorof(carcls))
		self.assertTrue(objectcls.hprof_ancestorof(bikecls))
		self.assertTrue(objectcls.hprof_ancestorof(limocls))

		self.assertFalse(vehiclecls.hprof_ancestorof(classcls))
		self.assertFalse(vehiclecls.hprof_ancestorof(maincls))
		self.assertFalse(vehiclecls.hprof_ancestorof(objectcls))
		self.assertTrue( vehiclecls.hprof_ancestorof(vehiclecls))
		self.assertTrue( vehiclecls.hprof_ancestorof(carcls))
		self.assertTrue( vehiclecls.hprof_ancestorof(bikecls))
		self.assertTrue( vehiclecls.hprof_ancestorof(limocls))

		self.assertFalse(carcls.hprof_ancestorof(classcls))
		self.assertFalse(carcls.hprof_ancestorof(maincls))
		self.assertFalse(carcls.hprof_ancestorof(objectcls))
		self.assertFalse(carcls.hprof_ancestorof(vehiclecls))
		self.assertTrue( carcls.hprof_ancestorof(carcls))
		self.assertFalse(carcls.hprof_ancestorof(bikecls))
		self.assertTrue( carcls.hprof_ancestorof(limocls))

		self.assertFalse(bikecls.hprof_ancestorof(classcls))
		self.assertFalse(bikecls.hprof_ancestorof(maincls))
		self.assertFalse(bikecls.hprof_ancestorof(objectcls))
		self.assertFalse(bikecls.hprof_ancestorof(vehiclecls))
		self.assertFalse(bikecls.hprof_ancestorof(carcls))
		self.assertTrue( bikecls.hprof_ancestorof(bikecls))
		self.assertFalse(bikecls.hprof_ancestorof(limocls))

		self.assertFalse(limocls.hprof_ancestorof(classcls))
		self.assertFalse(limocls.hprof_ancestorof(maincls))
		self.assertFalse(limocls.hprof_ancestorof(objectcls))
		self.assertFalse(limocls.hprof_ancestorof(vehiclecls))
		self.assertFalse(limocls.hprof_ancestorof(carcls))
		self.assertFalse(limocls.hprof_ancestorof(bikecls))
		self.assertTrue( limocls.hprof_ancestorof(limocls))

	def test_instanceof_classes(self):
		classcls = self.dump.get_class('java.lang.Class')
		maincls = self.dump.get_class('Main')
		objectcls = self.dump.get_class('java.lang.Object')
		vehiclecls = self.dump.get_class('com.example.cars.Vehicle')
		carcls = self.dump.get_class('com.example.cars.Car')
		bikecls = self.dump.get_class('com.example.cars.Bike')
		limocls = self.dump.get_class('com.example.cars.Limo')

		self.assertTrue(classcls  .hprof_instanceof(classcls))
		self.assertTrue(maincls   .hprof_instanceof(classcls))
		self.assertTrue(objectcls .hprof_instanceof(classcls))
		self.assertTrue(vehiclecls.hprof_instanceof(classcls))
		self.assertTrue(carcls    .hprof_instanceof(classcls))
		self.assertTrue(bikecls   .hprof_instanceof(classcls))
		self.assertTrue(limocls   .hprof_instanceof(classcls))

		self.assertTrue(classcls  .hprof_instanceof(objectcls))
		self.assertTrue(maincls   .hprof_instanceof(objectcls))
		self.assertTrue(objectcls .hprof_instanceof(objectcls))
		self.assertTrue(vehiclecls.hprof_instanceof(objectcls))
		self.assertTrue(carcls    .hprof_instanceof(objectcls))
		self.assertTrue(bikecls   .hprof_instanceof(objectcls))
		self.assertTrue(limocls   .hprof_instanceof(objectcls))

		self.assertFalse(classcls  .hprof_instanceof(vehiclecls))
		self.assertFalse(maincls   .hprof_instanceof(vehiclecls))
		self.assertFalse(objectcls .hprof_instanceof(vehiclecls))
		self.assertFalse(vehiclecls.hprof_instanceof(vehiclecls))
		self.assertFalse(carcls    .hprof_instanceof(vehiclecls))
		self.assertFalse(bikecls   .hprof_instanceof(vehiclecls))
		self.assertFalse(limocls   .hprof_instanceof(vehiclecls))

	def test_instanceof_objects(self):
		classcls = self.dump.get_class('java.lang.Class')
		carexcls = self.dump.get_class('com.example.cars.CarExample')
		objectcls = self.dump.get_class('java.lang.Object')
		vehiclecls = self.dump.get_class('com.example.cars.Vehicle')
		carcls = self.dump.get_class('com.example.cars.Car')
		bikecls = self.dump.get_class('com.example.cars.Bike')
		limocls = self.dump.get_class('com.example.cars.Limo')

		carex = next(self.dump.find_instances(carexcls, False))
		car = next(self.dump.find_instances(carcls, False))
		bike = next(self.dump.find_instances(bikecls, False))
		limo = next(self.dump.find_instances(limocls, False))

		self.assertFalse(carex.hprof_instanceof(classcls))
		self.assertTrue( carex.hprof_instanceof(carexcls))
		self.assertTrue( carex.hprof_instanceof(objectcls))
		self.assertFalse(carex.hprof_instanceof(vehiclecls))
		self.assertFalse(carex.hprof_instanceof(carcls))
		self.assertFalse(carex.hprof_instanceof(bikecls))
		self.assertFalse(carex.hprof_instanceof(limocls))

		self.assertFalse(car.hprof_instanceof(classcls))
		self.assertFalse(car.hprof_instanceof(carexcls))
		self.assertTrue( car.hprof_instanceof(objectcls))
		self.assertTrue( car.hprof_instanceof(vehiclecls))
		self.assertTrue( car.hprof_instanceof(carcls))
		self.assertFalse(car.hprof_instanceof(bikecls))
		self.assertFalse(car.hprof_instanceof(limocls))

		self.assertFalse(bike.hprof_instanceof(classcls))
		self.assertFalse(bike.hprof_instanceof(carexcls))
		self.assertTrue( bike.hprof_instanceof(objectcls))
		self.assertTrue( bike.hprof_instanceof(vehiclecls))
		self.assertFalse(bike.hprof_instanceof(carcls))
		self.assertTrue( bike.hprof_instanceof(bikecls))
		self.assertFalse(bike.hprof_instanceof(limocls))

		self.assertFalse(limo.hprof_instanceof(classcls))
		self.assertFalse(limo.hprof_instanceof(carexcls))
		self.assertTrue( limo.hprof_instanceof(objectcls))
		self.assertTrue( limo.hprof_instanceof(vehiclecls))
		self.assertTrue( limo.hprof_instanceof(carcls))
		self.assertFalse(limo.hprof_instanceof(bikecls))
		self.assertTrue( limo.hprof_instanceof(limocls))

	def test_instanceof_object_arrays(self):
		classcls = self.dump.get_class('java.lang.Class')
		objectcls = self.dump.get_class('java.lang.Object')
		arraycls = self.dump.get_class('java.lang.Object[]')
		vehiclecls = self.dump.get_class('com.example.cars.Vehicle')
		carex, = self.dump.find_instances('com.example.cars.CarExample')
		objs = carex.objs
		self.assertTrue(objs.hprof_instanceof(objectcls))
		self.assertTrue(objs.hprof_instanceof(arraycls))
		self.assertFalse(objs.hprof_instanceof(classcls))
		self.assertFalse(objs.hprof_instanceof(vehiclecls))

	def test_instanceof_primitive_arrays(self):
		classcls = self.dump.get_class('java.lang.Class')
		objectcls = self.dump.get_class('java.lang.Object')
		shortarrarr = self.dump.get_class('short[][]')
		shortarr = self.dump.get_class('short[]')
		vehiclecls = self.dump.get_class('com.example.cars.Vehicle')
		car = next(self.dump.find_instances('com.example.cars.Car', False))
		array = car.wheelDimensions

		# array is short[][] (so, actually an object array)
		self.assertFalse(array.hprof_instanceof(classcls))
		self.assertTrue( array.hprof_instanceof(objectcls))
		self.assertTrue( array.hprof_instanceof(shortarrarr))
		self.assertFalse(array.hprof_instanceof(shortarr))
		self.assertFalse(array.hprof_instanceof(vehiclecls))

		# array is short[] (yay, an primitive array!)
		array = array[0]
		self.assertFalse(array.hprof_instanceof(classcls))
		self.assertTrue( array.hprof_instanceof(objectcls))
		self.assertFalse(array.hprof_instanceof(shortarrarr))
		self.assertTrue( array.hprof_instanceof(shortarr))
		self.assertFalse(array.hprof_instanceof(vehiclecls))
