# Copyright (C) 2019 Snild Dolkow
# Licensed under the LICENSE.

from unittest import TestCase

from .example_shadowing import TestShadowing
from .example_arrays import TestArrays
from .example_cars import TestCars

from . import util

import hprof

def setUpModule():
	global thefile
	print()
	thefile = hprof.open('testdata/example-android.hprof.bz2', util.progress('example-android'))
	print('example-android: file loaded!            ')

def tearDownModule():
	global thefile
	thefile.close()
	thefile = None

class AndroidTest(TestCase):
	@classmethod
	def setUpClass(self):
		self.hf = thefile

class TestShadowingAndroid(TestShadowing, AndroidTest): pass
class TestArraysAndroid(TestArrays, AndroidTest): pass
class TestCarsAndroid(TestCars, AndroidTest): pass
