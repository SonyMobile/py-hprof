from unittest import TestCase

import hprof

class TestJavaShadowExample(TestCase):
	FILE = 'tests/java.hprof'

	@classmethod
	def setUpClass(self):
		self.hf = hprof.open(self.FILE)
		self.dump, = self.hf.dumps()

	def test_read_base(self):
		cls = self.dump.get_class('com.example.shadowing.Base')
		self.assertEqual(cls.what, 3)
		obj, = self.dump.find_instances(cls, False)
		self.assertEqual(obj.what, 3)

	def test_read_shadow_instance(self):
		cls = self.dump.get_class('com.example.shadowing.ShadowI')
		with self.assertRaisesRegex(hprof.FieldNotFoundError, 'static.*what'):
			cls.what
		obj, = self.dump.find_instances(cls, False)
		self.assertEqual(obj.what, 9)

	def test_read_shadow_instance_instance(self):
		cls = self.dump.get_class('com.example.shadowing.ShadowII')
		with self.assertRaisesRegex(hprof.FieldNotFoundError, 'static.*what'):
			cls.what
		obj, = self.dump.find_instances(cls, False)
		self.assertEqual(obj.what, 11)

	def test_read_shadow_instance_static(self):
		cls = self.dump.get_class('com.example.shadowing.ShadowIS')
		self.assertEqual(cls.what, 12)
		obj, = self.dump.find_instances(cls, False)
		self.assertEqual(obj.what, 12)

	def test_read_shadow_static(self):
		cls = self.dump.get_class('com.example.shadowing.ShadowS')
		self.assertEqual(cls.what, 7)
		obj, = self.dump.find_instances(cls, False)
		self.assertEqual(obj.what, 7)

	def test_read_shadow_static_instance(self):
		cls = self.dump.get_class('com.example.shadowing.ShadowSI')
		with self.assertRaisesRegex(hprof.FieldNotFoundError, 'static.*what'):
			cls.what
		obj, = self.dump.find_instances(cls, False)
		self.assertEqual(obj.what, 100)

	def test_read_shadow_static_static(self):
		cls = self.dump.get_class('com.example.shadowing.ShadowSS')
		self.assertEqual(cls.what, 103)
		obj, = self.dump.find_instances(cls, False)
		self.assertEqual(obj.what, 103)

# TODO: in Java, lookups depend on the type of the _reference_. Should add some kind of wrapper to emulate that when possible (e.g. when reading from object arrays; won't be possible for normal reference attrs)
