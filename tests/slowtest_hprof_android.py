from .test_hprof_carexample import TestJavaCarExample
from .test_hprof_shadowexample import TestJavaShadowExample

import hprof

def setUpModule():
	global slowfile
	slowfile = hprof.open('tests/android.hprof')

def tearDownModule():
	global slowfile
	slowfile.close()
	slowfile = None

class TestAndroidCarExample(TestJavaCarExample):
	@classmethod
	def setUpClass(self):
		self.hf = slowfile

class TestAndroidShadowExample(TestJavaShadowExample):
	@classmethod
	def setUpClass(self):
		self.hf = slowfile
