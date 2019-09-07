import unittest

import hprof
from hprof import heap

class TestJavaClass(unittest.TestCase):
	def setUp(self):
		heap._add_class(self, 'java.lang.Object', None, ('shadow',))
		heap._add_class(self, 'java.lang.Class', self.java.lang.Object, ('secret',))
		heap._add_class(self.java, 'util.List', self.java.lang.Object, ('next',))
		heap._add_class(self, 'Shadower', self.java.util.List, ('shadow','unique'))

	def test_duplicate_class(self):
		with self.assertRaises(ValueError):
			heap._add_class(self, 'java.lang.Class', self.java.lang.Object, ('secret',))

	def test_setup_basics(self):
		self.assertIsInstance(self.java, heap.JavaPackage)
		self.assertIsInstance(self.java.lang, heap.JavaPackage)
		self.assertIsInstance(self.java.util, heap.JavaPackage)

		self.assertFalse(issubclass(self.java.lang.Object, self.java.lang.Class))
		self.assertFalse(issubclass(self.java.lang.Object, self.java.util.List))
		self.assertFalse(issubclass(self.java.lang.Object, self.Shadower))
		self.assertTrue( issubclass(self.java.lang.Class,  self.java.lang.Object))
		self.assertFalse(issubclass(self.java.lang.Class,  self.java.util.List))
		self.assertFalse(issubclass(self.java.lang.Class,  self.Shadower))
		self.assertTrue( issubclass(self.java.util.List,   self.java.lang.Object))
		self.assertFalse(issubclass(self.java.util.List,   self.java.lang.Class))
		self.assertFalse(issubclass(self.java.util.List,   self.Shadower))
		self.assertTrue( issubclass(self.Shadower,         self.java.lang.Object))
		self.assertFalse(issubclass(self.Shadower,         self.java.lang.Class))
		self.assertTrue( issubclass(self.Shadower,         self.java.util.List))

		self.assertIsInstance(self.java.lang.Object, heap.JavaClass)
		self.assertIsInstance(self.java.lang.Class,  heap.JavaClass)
		self.assertIsInstance(self.java.util.List,   heap.JavaClass)
		self.assertIsInstance(self.Shadower,         heap.JavaClass)

	def test_package_str(self):
		self.assertEqual(str(self.java),      'java')
		self.assertEqual(str(self.java.lang), 'java.lang')
		self.assertEqual(str(self.java.util), 'java.util')

	def test_package_repr(self):
		self.assertEqual(repr(self.java),      "<JavaPackage 'java'>")
		self.assertEqual(repr(self.java.lang), "<JavaPackage 'java.lang'>")
		self.assertEqual(repr(self.java.util), "<JavaPackage 'java.util'>")

	def test_class_str(self):
		self.assertEqual(str(self.java.lang.Object), 'java.lang.Object')
		self.assertEqual(str(self.java.lang.Class),  'java.lang.Class')
		self.assertEqual(str(self.java.util.List),   'java.util.List')
		self.assertEqual(str(self.Shadower),         'Shadower')

	def test_class_repr(self):
		self.assertEqual(repr(self.java.lang.Object), "<JavaClass 'java.lang.Object'>")
		self.assertEqual(repr(self.java.lang.Class),  "<JavaClass 'java.lang.Class'>")
		self.assertEqual(repr(self.Shadower),         "<JavaClass 'Shadower'>")

	def test_object_instance(self):
		o = self.java.lang.Object(0xf00d)
		with self.assertRaises(AttributeError):
			o.blah = 3
		o.shadow = 3
		self.assertEqual(o.shadow, 3)
		self.assertIsInstance(o, heap.JavaObject)
		self.assertIsInstance(o, self.java.lang.Object)
		self.assertNotIsInstance(o, self.java.lang.Class)
		self.assertNotIsInstance(o, self.java.util.List)
		self.assertEqual(str(o), '<java.lang.Object 0xf00d>')
		self.assertEqual(repr(o), str(o))
		self.assertCountEqual(dir(o), ('shadow',))

	def test_class_instance(self):
		c = self.java.lang.Class(0xdead)
		with self.assertRaises(AttributeError):
			c.next = 3
		c.shadow = 72
		c.secret = 78
		self.assertEqual(c.shadow, 72)
		self.assertEqual(c.secret, 78)
		self.assertIsInstance(c, heap.JavaObject)
		self.assertIsInstance(c, self.java.lang.Object)
		self.assertIsInstance(c, self.java.lang.Class)
		self.assertNotIsInstance(c, self.java.util.List)
		self.assertEqual(str(c), '<java.lang.Class 0xdead>')
		self.assertEqual(repr(c), str(c))
		self.assertCountEqual(dir(c), ('shadow', 'secret'))

	def test_static_vars(self):
		c = self.java.lang.Class(11)
		l = self.java.util.List(22)
		self.java.lang.Object.sGlobalLock = 10
		self.assertEqual(self.java.lang.Object.sGlobalLock, 10)
		self.assertEqual(self.java.lang.Class.sGlobalLock, 10)
		self.assertEqual(self.java.util.List.sGlobalLock, 10)
		self.assertEqual(c.sGlobalLock, 10)
		self.assertEqual(l.sGlobalLock, 10)
		self.java.util.List.sGlobalLock = 20 # shadow the one in Object
		self.assertEqual(self.java.lang.Object.sGlobalLock, 10)
		self.assertEqual(self.java.lang.Class.sGlobalLock, 10)
		self.assertEqual(self.java.util.List.sGlobalLock, 20)
		self.assertEqual(c.sGlobalLock, 10)
		self.assertEqual(l.sGlobalLock, 20)

	def test_refs(self):
		heap._add_class(self, 'Extra', self.Shadower, ('shadow',))
		e = self.Extra(0xbadf00d)
		self.java.lang.Object.shadow.__set__(e, 1111)
		self.Shadower.shadow.__set__(e, 2223)
		e.shadow = 10
		e.unique = 33
		e.next = 708

		self.assertEqual(e.shadow, 10)
		self.assertEqual(e.unique, 33)
		self.assertEqual(e.next, 708)
		self.assertCountEqual(dir(e), ('shadow', 'unique', 'next'))
		self.assertEqual(str(e), '<Extra 0xbadf00d>')
		self.assertEqual(repr(e), str(e))

		r = heap.Ref(e, self.Extra)
		self.assertIs(r, e) # no reason to use Ref when reftype matches exactly.

		s = hprof.cast(e, self.Shadower)
		self.assertEqual(s, e)
		self.assertEqual(s.shadow, 2223)
		self.assertEqual(s.unique, 33)
		self.assertEqual(s.next, 708)
		self.assertCountEqual(dir(s), ('shadow', 'unique', 'next'))
		self.assertEqual(str(s), '<Ref of type Shadower to Extra 0xbadf00d>')
		self.assertEqual(repr(s), str(s))
		self.assertIsInstance(s, self.java.lang.Object)
		self.assertIsInstance(s, self.java.util.List)
		self.assertIsInstance(s, self.Shadower)
		self.assertIsInstance(s, self.Extra)
		self.assertNotIsInstance(s, self.java.lang.Class)

		l = hprof.cast(e, self.java.util.List)
		self.assertEqual(l.shadow, 1111)
		self.assertEqual(l, e)
		with self.assertRaises(AttributeError):
			self.assertEqual(l.unique, 33)
		self.assertEqual(l.next, 708)
		self.assertCountEqual(dir(l), ('shadow', 'next'))
		self.assertEqual(str(l), '<Ref of type java.util.List to Extra 0xbadf00d>')
		self.assertEqual(repr(l), str(l))
		self.assertIsInstance(l, self.java.lang.Object)
		self.assertIsInstance(l, self.java.util.List)
		self.assertIsInstance(l, self.Shadower)
		self.assertIsInstance(l, self.Extra)
		self.assertNotIsInstance(l, self.java.lang.Class)

		o = hprof.cast(e, self.java.lang.Object)
		self.assertEqual(o, e)
		self.assertEqual(o.shadow, 1111)
		with self.assertRaises(AttributeError):
			self.assertEqual(o.unique, 33)
		with self.assertRaises(AttributeError):
			self.assertEqual(o.next, 708)
		self.assertCountEqual(dir(o), ('shadow',))
		self.assertEqual(str(o), '<Ref of type java.lang.Object to Extra 0xbadf00d>')
		self.assertEqual(repr(o), str(o))
		self.assertIsInstance(o, self.java.lang.Object)
		self.assertIsInstance(o, self.java.util.List)
		self.assertIsInstance(o, self.Shadower)
		self.assertIsInstance(o, self.Extra)
		self.assertNotIsInstance(o, self.java.lang.Class)

	def test_casting(self):
		s = self.Shadower(1001)
		l = hprof.cast(s, self.java.util.List)
		o = hprof.cast(s, self.java.lang.Object)
		# casting upward
		self.assertIs(hprof.cast(s, self.Shadower), s)
		self.assertEqual(hprof.cast(s, self.java.util.List), s)
		self.assertEqual(hprof.cast(s, self.java.lang.Object), s)
		# casting downward
		self.assertEqual(hprof.cast(o, self.java.lang.Object), s)
		self.assertEqual(hprof.cast(o, self.java.util.List), s)
		self.assertIs(hprof.cast(o, self.Shadower), s)

	def test_bad_cast(self):
		s = self.Shadower(1020)
		with self.assertRaises(TypeError):
			hprof.cast(s, self.java.lang.Class)

	def test_bad_downcast(self):
		s = self.Shadower(1033)
		o = hprof.cast(s, self.java.lang.Object)
		with self.assertRaises(TypeError):
			hprof.cast(o, self.java.lang.Class)

	def test_unref(self):
		s = self.Shadower(1234)
		o = hprof.cast(s, self.java.lang.Object)
		self.assertIs(hprof.cast(o), s)

	def test_refs_to_class(self):
		heap._add_class(self, 'java.lang.String', self.java.lang.Object, ('chars',))
		o = hprof.cast(self.java.lang.String, self.java.lang.Object)
		c = hprof.cast(self.java.lang.String, self.java.lang.Class)
		self.assertIs(o, self.java.lang.String)
		self.assertIs(c, self.java.lang.String)
		with self.assertRaises(TypeError):
			hprof.cast(self.java.lang.String, self.java.lang.String)
		with self.assertRaises(TypeError):
			hprof.cast(self.java.lang.String, self.java.util.List)
