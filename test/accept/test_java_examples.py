from unittest import TestCase

from .example_shadowing import TestShadowing

import hprof

def setUpModule():
	global thefile
	thefile = hprof.open('testdata/example-java.hprof.bz2')

def tearDownModule():
	global thefile
	thefile.close()
	thefile = None

class TestShadowingJvm(TestShadowing, TestCase):
	@classmethod
	def setUpClass(self):
		self.hf = thefile
