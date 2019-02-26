from unittest import TestCase

import hprof

class TestJavaCarExample(TestCase):
	FILE = 'tests/java.hprof'

	@classmethod
	def setUpClass(self):
		self.hf = hprof.open(self.FILE)
		self.dump, = self.hf.dumps()

	def test_find_class_by_name(self):
		main  = self.dump.get_class('Main')
		carex = self.dump.get_class('com.example.cars.CarExample')
		self.assertIs(type(main),  hprof.heap.Class)
		self.assertIs(type(carex), hprof.heap.Class)
		self.assertEqual(main.hprof_name, 'Main')
		self.assertEqual(carex.hprof_name, 'com.example.cars.CarExample')
