from unittest import TestCase

from .example_shadowing import TestShadowing

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

class TestShadowingJvm(TestShadowing, TestCase):
	@classmethod
	def setUpClass(self):
		self.hf = thefile
