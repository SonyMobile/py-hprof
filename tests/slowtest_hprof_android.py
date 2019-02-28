from .test_hprof_carexample import TestJavaCarExample
from .test_hprof_shadowexample import TestJavaShadowExample

class TestAndroidCarExample(TestJavaCarExample):
	FILE = 'tests/android.hprof'

class TestAndroidShadowExample(TestJavaShadowExample):
	FILE = 'tests/android.hprof'
