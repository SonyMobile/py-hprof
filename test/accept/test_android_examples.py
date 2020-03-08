from unittest import TestCase

from .example_shadowing import TestShadowing

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

class TestShadowingAndroid(TestShadowing, TestCase):
	@classmethod
	def setUpClass(self):
		self.hf = thefile
