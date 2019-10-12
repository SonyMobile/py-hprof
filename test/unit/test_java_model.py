import unittest

import hprof
from hprof import heap

class TestJavaClass(unittest.TestCase):
	def setUp(self):
		self.obj = heap._create_class(self, 'java/lang/Object', None, ('shadow',))
		self.cls = heap._create_class(self, 'java/lang/Class', self.obj, ('secret',))
		self.lst = heap._create_class(self, 'java/util/List', self.obj, ('next',))
		self.inr = heap._create_class(self, 'java/util/List$Inner', self.obj, ('this$0',))
		self.shd = heap._create_class(self, 'Shadower', self.lst, ('shadow','unique'))

	def test_duplicate_class(self):
		old = self.java.lang.Class
		newcls = heap._create_class(self, 'java/lang/Class', self.obj, ('secret',))
		self.assertIs(old, self.java.lang.Class) # same name object
		self.assertIsNot(newcls, self.cls)

	def test_setup_basics(self):
		self.assertIsInstance(self.java, heap.JavaPackage)
		self.assertIsInstance(self.java.lang, heap.JavaPackage)
		self.assertIsInstance(self.java.util, heap.JavaPackage)

		self.assertFalse(issubclass(self.obj, self.cls))
		self.assertFalse(issubclass(self.obj, self.lst))
		self.assertFalse(issubclass(self.obj, self.inr))
		self.assertFalse(issubclass(self.obj, self.shd))
		self.assertTrue( issubclass(self.cls, self.obj))
		self.assertFalse(issubclass(self.cls, self.lst))
		self.assertFalse(issubclass(self.cls, self.inr))
		self.assertFalse(issubclass(self.cls, self.shd))
		self.assertTrue( issubclass(self.lst, self.obj))
		self.assertFalse(issubclass(self.lst, self.cls))
		self.assertFalse(issubclass(self.lst, self.inr))
		self.assertFalse(issubclass(self.lst, self.shd))
		self.assertTrue( issubclass(self.inr, self.obj))
		self.assertFalse(issubclass(self.inr, self.cls))
		self.assertFalse(issubclass(self.inr, self.lst))
		self.assertFalse(issubclass(self.inr, self.shd))
		self.assertTrue( issubclass(self.shd, self.obj))
		self.assertFalse(issubclass(self.shd, self.cls))
		self.assertTrue( issubclass(self.shd, self.lst))
		self.assertFalse(issubclass(self.shd, self.inr))

		self.assertIsInstance(self.obj, heap.JavaClass)
		self.assertIsInstance(self.cls, heap.JavaClass)
		self.assertIsInstance(self.lst, heap.JavaClass)
		self.assertIsInstance(self.inr, heap.JavaClass)
		self.assertIsInstance(self.shd, heap.JavaClass)

	def test_package_eq(self):
		self.assertEqual(self.java,      'java')
		self.assertEqual(self.java.lang, 'java.lang')
		self.assertEqual(self.java.util, 'java.util')

	def test_package_str(self):
		self.assertEqual(str(self.java),      'java')
		self.assertEqual(str(self.java.lang), 'java.lang')
		self.assertEqual(str(self.java.util), 'java.util')

	def test_package_repr(self):
		self.assertEqual(repr(self.java),      "<JavaPackage 'java'>")
		self.assertEqual(repr(self.java.lang), "<JavaPackage 'java.lang'>")
		self.assertEqual(repr(self.java.util), "<JavaPackage 'java.util'>")

	def test_class_name_eq(self):
		self.assertEqual(self.java.lang.Object,     'java.lang.Object')
		self.assertEqual(self.java.lang.Class,      'java.lang.Class')
		self.assertEqual(self.java.util.List,       'java.util.List')
		self.assertEqual(self.java.util.List.Inner, 'java.util.List.Inner')
		self.assertEqual(self.Shadower,             'Shadower')

	def test_class_name_hash(self):
		self.assertEqual(hash(self.java.lang.Object),     hash('java.lang.Object'))
		self.assertEqual(hash(self.java.lang.Class),      hash('java.lang.Class'))
		self.assertEqual(hash(self.java.util.List),       hash('java.util.List'))
		self.assertEqual(hash(self.java.util.List.Inner), hash('java.util.List.Inner'))
		self.assertEqual(hash(self.Shadower),             hash('Shadower'))

	def test_class_str(self):
		self.assertEqual(str(self.obj), "java.lang.Object")
		self.assertEqual(str(self.cls), "java.lang.Class")
		self.assertEqual(str(self.lst), "java.util.List")
		self.assertEqual(str(self.inr), "java.util.List.Inner")
		self.assertEqual(str(self.shd), "Shadower")

	def test_class_name_str(self):
		self.assertEqual(str(self.java.lang.Object),     'java.lang.Object')
		self.assertEqual(str(self.java.lang.Class),      'java.lang.Class')
		self.assertEqual(str(self.java.util.List),       'java.util.List')
		self.assertEqual(str(self.java.util.List.Inner), 'java.util.List.Inner')
		self.assertEqual(str(self.Shadower),             'Shadower')

	def test_class_repr(self):
		self.assertEqual(repr(self.obj), "<JavaClass 'java.lang.Object'>")
		self.assertEqual(repr(self.cls), "<JavaClass 'java.lang.Class'>")
		self.assertEqual(repr(self.lst), "<JavaClass 'java.util.List'>")
		self.assertEqual(repr(self.inr), "<JavaClass 'java.util.List.Inner'>")
		self.assertEqual(repr(self.shd), "<JavaClass 'Shadower'>")

	def test_class_name_repr(self):
		self.assertEqual(repr(self.java.lang.Object),     "<JavaClassName 'java.lang.Object'>")
		self.assertEqual(repr(self.java.lang.Class),      "<JavaClassName 'java.lang.Class'>")
		self.assertEqual(repr(self.java.util.List),       "<JavaClassName 'java.util.List'>")
		self.assertEqual(repr(self.java.util.List.Inner), "<JavaClassName 'java.util.List.Inner'>")
		self.assertEqual(repr(self.Shadower),             "<JavaClassName 'Shadower'>")

	def test_object_instance(self):
		o = self.obj(0xf00d)
		with self.assertRaises(AttributeError):
			o.blah = 3
		self.obj._hprof_ifieldvals.__set__(o, (3,))
		self.assertEqual(o.shadow, 3)
		self.assertIsInstance(o, heap.JavaObject)
		self.assertIsInstance(o, self.obj)
		self.assertNotIsInstance(o, self.cls)
		self.assertNotIsInstance(o, self.lst)
		self.assertEqual(str(o), '<java.lang.Object 0xf00d>')
		self.assertEqual(repr(o), str(o))
		self.assertCountEqual(dir(o), ('shadow',))
		with self.assertRaisesRegex(TypeError, 'has no len'):
			len(o)
		with self.assertRaisesRegex(TypeError, 'not an array type'):
			o[3]

	def test_class_instance(self):
		c = self.cls(0xdead)
		with self.assertRaises(AttributeError):
			c.next = 3
		self.obj._hprof_ifieldvals.__set__(c, (72,))
		self.cls._hprof_ifieldvals.__set__(c, (78,))
		self.assertEqual(c.shadow, 72)
		self.assertEqual(c.secret, 78)
		self.assertIsInstance(c, heap.JavaObject)
		self.assertIsInstance(c, self.obj)
		self.assertIsInstance(c, self.cls)
		self.assertNotIsInstance(c, self.lst)
		self.assertEqual(str(c), '<java.lang.Class 0xdead>')
		self.assertEqual(repr(c), str(c))
		self.assertCountEqual(dir(c), ('shadow', 'secret'))

	def test_inner_instance(self):
		i = self.inr(0x1)
		with self.assertRaises(AttributeError):
			i.missing
		self.obj._hprof_ifieldvals.__set__(i, (101,))
		self.inr._hprof_ifieldvals.__set__(i, (102,))
		self.assertEqual(i.shadow, 101)
		self.assertEqual(getattr(i, 'this$0'), 102)
		self.assertIsInstance(i, heap.JavaObject)
		self.assertIsInstance(i, self.obj)
		self.assertIsInstance(i, self.inr)
		self.assertNotIsInstance(i, self.lst)
		self.assertEqual(str(i), '<java.util.List.Inner 0x1>')
		self.assertEqual(repr(i), str(i))
		self.assertCountEqual(dir(i), ('shadow', 'this$0'))


	def test_double_dollar(self):
		lambdacls = heap._create_class(self, 'com/example/Vehicle$$Lambda$1/455659002', self.obj, ('closure_x', 'closure_y'))
		self.assertEqual(str(lambdacls), 'com.example.Vehicle$$Lambda$1/455659002')
		lambdaobj = lambdacls(33)
		self.obj._hprof_ifieldvals.__set__(lambdaobj, (11,))
		lambdacls._hprof_ifieldvals.__set__(lambdaobj, (10, 20))
		with self.assertRaises(AttributeError):
			lambdaobj.missing
		with self.assertRaises(AttributeError):
			lambdaobj.missing = 3
		with self.assertRaises(AttributeError):
			lambdaobj.closure_x = 3
		self.assertEqual(lambdaobj.shadow, 11)
		self.assertEqual(lambdaobj.closure_x, 10)
		self.assertEqual(lambdaobj.closure_y, 20)
		self.assertIsInstance(lambdaobj, heap.JavaObject)
		self.assertIsInstance(lambdaobj, self.obj)
		self.assertIsInstance(lambdaobj, lambdacls)
		self.assertEqual(str(lambdaobj), '<com.example.Vehicle$$Lambda$1/455659002 0x21>')
		self.assertEqual(repr(lambdaobj), str(lambdaobj))
		self.assertCountEqual(dir(lambdaobj), ('shadow', 'closure_x', 'closure_y'))

	def test_obj_array(self):
		# the base array class...
		oacls = heap._create_array_class(self, '[Ljava/lang/Object;', self.obj, ('extrastuff',))
		self.assertEqual(str(oacls), 'java.lang.Object[]')
		self.assertEqual(repr(oacls), "<JavaClass 'java.lang.Object[]'>")
		self.assertTrue(isinstance(oacls, heap.JavaClass))
		self.assertTrue(isinstance(oacls, heap.JavaArrayClass))
		self.assertTrue(issubclass(oacls, heap.JavaObject))
		self.assertTrue(issubclass(oacls, self.obj))

		oarr = oacls(73)
		oarr._hprof_ifieldvals = (49,)
		oarr._hprof_array_data = (10, 55, 33)
		self.assertEqual(len(oarr), 3)
		self.assertEqual(oarr[0], 10)
		self.assertEqual(oarr[1], 55)
		self.assertEqual(oarr[2], 33)
		self.assertEqual(oarr[-1], 33)
		self.assertEqual(oarr[-2], 55)
		self.assertEqual(oarr[-3], 10)
		self.assertEqual(oarr[:], (10, 55, 33))
		self.assertEqual(oarr[1:], (55, 33))
		self.assertEqual(oarr[:2], (10, 55))
		self.assertEqual(oarr[:-1], (10, 55))
		self.assertEqual(oarr[2:], (33,))
		self.assertEqual(oarr[:0], ())
		self.assertEqual(oarr[:1], (10,))
		with self.assertRaises(IndexError):
			oarr[3]
		with self.assertRaises(IndexError):
			oarr[-4]
		with self.assertRaises(TypeError):
			oarr['hello']
		self.assertIn(10, oarr)
		self.assertIn(55, oarr)
		self.assertIn(33, oarr)
		self.assertNotIn(11, oarr)
		self.assertNotIn(12, oarr)
		self.assertNotIn(49, oarr)
		self.assertNotIn(32, oarr)
		for i, x in enumerate(oarr):
			self.assertEqual(x, oarr[i])
		self.assertEqual(i, 2)
		self.assertEqual(oarr.extrastuff, 49)

		# ...and a subclass
		lacls = heap._create_array_class(self, '[LList$$lambda;', oacls, ('more',))
		self.assertEqual(str(lacls), 'List$$lambda[]')
		self.assertEqual(repr(lacls), "<JavaClass 'List$$lambda[]'>")
		self.assertTrue(isinstance(lacls, heap.JavaClass))
		self.assertTrue(isinstance(lacls, heap.JavaArrayClass))
		self.assertTrue(issubclass(lacls, heap.JavaObject))
		self.assertTrue(issubclass(lacls, self.obj))
		self.assertTrue(issubclass(lacls, oacls))

		larr = lacls(97)
		oacls._hprof_ifieldvals.__set__(larr, (56,))
		lacls._hprof_ifieldvals.__set__(larr, (99,))
		larr._hprof_array_data = (1, 3, 5, 7, 9)
		self.assertEqual(len(larr), 5)
		self.assertEqual(larr[0], 1)
		self.assertEqual(larr[1], 3)
		self.assertEqual(larr[2], 5)
		self.assertEqual(larr[3], 7)
		self.assertEqual(larr[4], 9)
		self.assertEqual(larr[-1], 9)
		self.assertEqual(larr[-2], 7)
		self.assertEqual(larr[-3], 5)
		self.assertEqual(larr[-4], 3)
		self.assertEqual(larr[-5], 1)
		self.assertEqual(larr[:], (1,3,5,7,9))
		self.assertEqual(larr[1:], (3,5,7,9))
		self.assertEqual(larr[:2], (1,3))
		self.assertEqual(larr[:-1], (1,3,5,7))
		self.assertEqual(larr[2:], (5,7,9))
		self.assertEqual(larr[:0], ())
		self.assertEqual(larr[:1], (1,))
		with self.assertRaises(IndexError):
			larr[5]
		with self.assertRaises(IndexError):
			larr[-6]
		with self.assertRaises(TypeError):
			larr['world']
		self.assertIn(1, larr)
		self.assertIn(3, larr)
		self.assertIn(5, larr)
		self.assertIn(7, larr)
		self.assertIn(9, larr)
		self.assertNotIn(0, larr)
		self.assertNotIn(2, larr)
		self.assertNotIn(4, larr)
		self.assertNotIn(6, larr)
		self.assertNotIn(8, larr)
		self.assertNotIn(100, larr)
		for i, x in enumerate(larr):
			self.assertEqual(x, larr[i])
		self.assertEqual(i, 4)
		self.assertEqual(larr.extrastuff, 56)
		self.assertEqual(larr.more, 99)

	def test_static_vars(self):
		c = self.cls(11)
		l = self.lst(22)
		self.obj._hprof_sfields['sGlobalLock'] = 10
		self.assertEqual(self.obj.sGlobalLock, 10)
		self.assertEqual(self.cls.sGlobalLock, 10)
		self.assertEqual(self.lst.sGlobalLock, 10)
		self.assertEqual(c.sGlobalLock, 10)
		self.assertEqual(l.sGlobalLock, 10)
		self.lst._hprof_sfields['sGlobalLock'] = 20 # shadow the one in Object
		self.assertEqual(self.obj.sGlobalLock, 10)
		self.assertEqual(self.cls.sGlobalLock, 10)
		self.assertEqual(self.lst.sGlobalLock, 20)
		self.assertEqual(c.sGlobalLock, 10)
		self.assertEqual(l.sGlobalLock, 20)
		with self.assertRaises(AttributeError):
			self.obj.sMissing
		with self.assertRaises(AttributeError):
			self.cls.sMissing
		with self.assertRaises(AttributeError):
			self.lst.sMissing
		with self.assertRaises(AttributeError):
			self.c.sMissing
		with self.assertRaises(AttributeError):
			self.l.sMissing

	def test_refs(self):
		extraclass = heap._create_class(self, 'Extra', self.shd, ('shadow',))
		e = extraclass(0xbadf00d)
		self.obj._hprof_ifieldvals.__set__(e, (1111,))
		self.lst._hprof_ifieldvals.__set__(e, (708,))
		self.shd._hprof_ifieldvals.__set__(e, (2223, 33))
		extraclass._hprof_ifieldvals.__set__(e, (10,))

		self.assertEqual(e.shadow, 10)
		self.assertEqual(e.unique, 33)
		self.assertEqual(e.next, 708)
		self.assertCountEqual(dir(e), ('shadow', 'unique', 'next'))
		self.assertEqual(str(e), '<Extra 0xbadf00d>')
		self.assertEqual(repr(e), str(e))

		r = heap.Ref(e, extraclass)
		self.assertIs(r, e) # no reason to use Ref when reftype matches exactly.

		s = hprof.cast(e, self.shd)
		self.assertEqual(s, e)
		self.assertEqual(s.shadow, 2223)
		self.assertEqual(s.unique, 33)
		self.assertEqual(s.next, 708)
		self.assertCountEqual(dir(s), ('shadow', 'unique', 'next'))
		self.assertEqual(str(s), '<Ref of type Shadower to Extra 0xbadf00d>')
		self.assertEqual(repr(s), str(s))
		self.assertIsInstance(s, self.obj)
		self.assertIsInstance(s, self.lst)
		self.assertIsInstance(s, self.shd)
		self.assertIsInstance(s, extraclass)
		self.assertNotIsInstance(s, self.cls)

		l = hprof.cast(e, self.lst)
		self.assertEqual(l.shadow, 1111)
		self.assertEqual(l, e)
		with self.assertRaises(AttributeError):
			self.assertEqual(l.unique, 33)
		self.assertEqual(l.next, 708)
		self.assertCountEqual(dir(l), ('shadow', 'next'))
		self.assertEqual(str(l), '<Ref of type java.util.List to Extra 0xbadf00d>')
		self.assertEqual(repr(l), str(l))
		self.assertIsInstance(l, self.obj)
		self.assertIsInstance(l, self.lst)
		self.assertIsInstance(l, self.shd)
		self.assertIsInstance(l, extraclass)
		self.assertNotIsInstance(l, self.cls)

		o = hprof.cast(e, self.obj)
		self.assertEqual(o, e)
		self.assertEqual(o.shadow, 1111)
		with self.assertRaises(AttributeError):
			self.assertEqual(o.unique, 33)
		with self.assertRaises(AttributeError):
			self.assertEqual(o.next, 708)
		self.assertCountEqual(dir(o), ('shadow',))
		self.assertEqual(str(o), '<Ref of type java.lang.Object to Extra 0xbadf00d>')
		self.assertEqual(repr(o), str(o))
		self.assertIsInstance(o, self.obj)
		self.assertIsInstance(o, self.lst)
		self.assertIsInstance(o, self.shd)
		self.assertIsInstance(o, extraclass)
		self.assertNotIsInstance(o, self.cls)

	def test_casting(self):
		s = self.shd(1001)
		l = hprof.cast(s, self.lst)
		o = hprof.cast(s, self.obj)
		# casting upward
		self.assertIs(hprof.cast(s, self.shd), s)
		self.assertEqual(hprof.cast(s, self.lst), s)
		self.assertEqual(hprof.cast(s, self.obj), s)
		# casting downward
		self.assertEqual(hprof.cast(o, self.obj), s)
		self.assertEqual(hprof.cast(o, self.lst), s)
		self.assertIs(hprof.cast(o, self.shd), s)

	def test_bad_cast(self):
		s = self.shd(1020)
		with self.assertRaises(TypeError):
			hprof.cast(s, self.java.lang.Class)

	def test_bad_downcast(self):
		s = self.shd(1033)
		o = hprof.cast(s, self.obj)
		with self.assertRaises(TypeError):
			hprof.cast(o, self.cls)

	def test_unref(self):
		s = self.shd(1234)
		o = hprof.cast(s, self.obj)
		self.assertIs(hprof.cast(o), s)

	def test_refs_to_class(self):
		string = heap._create_class(self, 'java/lang/String', self.obj, ('chars',))
		o = hprof.cast(string, self.obj)
		c = hprof.cast(string, self.cls)
		self.assertIs(o, string)
		self.assertIs(c, string)
		with self.assertRaises(TypeError):
			hprof.cast(string, string)
		with self.assertRaises(TypeError):
			hprof.cast(string, self.lst)
