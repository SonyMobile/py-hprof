from unittest import TestCase

from .example_shadowing import TestShadowing
from .example_arrays import TestArrays
from .example_cars import TestCars

import hprof

from . import util

def setUpModule():
	global thefile
	print()
	thefile = hprof.open('testdata/example-java.hprof.bz2', util.progress('example-java'))
	print('example-java: file loaded!            ')

def tearDownModule():
	global thefile
	thefile.close()
	thefile = None

class JvmTest(TestCase):
	@classmethod
	def setUpClass(self):
		self.hf = thefile

class TestShadowingJvm(TestShadowing, JvmTest): pass
class TestArraysJvm(TestArrays, JvmTest): pass
class TestCarsJvm(TestCars, JvmTest): pass
