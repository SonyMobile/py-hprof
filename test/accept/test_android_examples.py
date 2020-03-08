from unittest import TestCase

from .example_shadowing import TestShadowing

import hprof

def setUpModule():
	global thefile
	thefile = hprof.open('testdata/example-android.hprof.bz2')

def tearDownModule():
	global thefile
	thefile.close()
	thefile = None

class TestShadowingAndroid(TestShadowing, TestCase):
	@classmethod
	def setUpClass(self):
		self.hf = thefile
