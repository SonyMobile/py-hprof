# Copyright (C) 2019 Snild Dolkow
# Licensed under the LICENSE.

import unittest
import hprof

from .util import varyingid

@varyingid
class TestParseClassLoadRecord(unittest.TestCase):

	def setUp(self):
		self.hf.names[self.id(0xdeadd00d)] = 'Kenny'
		self.hf.names[self.id(0xdeadbeef)] = 'Hamburger'
		self.dummytrace1 = 'dummy trace 1'
		self.hf.stacktraces[3] = self.dummytrace1
		self.dummytrace2 = 'dummy trace 2'
		self.hf.stacktraces[0x30] = self.dummytrace2

	def addload(self, serial, objid, stackserial, nameid):
		indata = self.build().u4(serial).id(objid).u4(stackserial).id(nameid)
		reader = hprof._parsing.PrimitiveReader(memoryview(indata), self.idsize)
		hprof._parsing.record_parsers[0x02](self.hf, reader, None)

	def test_lonely(self):
		self.addload(0x1, 0x2, 0x3, 0xdeadd00d)
		self.assertEqual(len(self.hf.classloads), 1)
		self.assertEqual(len(self.hf.classloads_by_id), 1)
		self.assertIn(1, self.hf.classloads)
		load = self.hf.classloads[1]
		self.assertIsInstance(load, hprof._parsing.ClassLoad)
		self.assertEqual(load.class_id, 2)
		self.assertEqual(load.stacktrace, 3)
		self.assertEqual(load.class_name, 'Kenny')
		self.assertIn(2, self.hf.classloads_by_id)
		self.assertIs(self.hf.classloads_by_id[2], load)
		hprof._parsing._resolve_references(self.hf, None)
		self.assertIs(load.stacktrace, self.dummytrace1)

	def test_multiple(self):
		self.addload(0x1, 0x2, 0x30, 0xdeadd00d)
		self.addload(0x97104329, 0x2021222324, 0x3, 0xdeadbeef)
		self.assertEqual(len(self.hf.classloads), 2)
		self.assertEqual(len(self.hf.classloads_by_id), 2)

		self.assertIn(1, self.hf.classloads)
		load1 = self.hf.classloads[1]
		self.assertIsInstance(load1, hprof._parsing.ClassLoad)
		self.assertEqual(load1.class_id, 2)
		self.assertEqual(load1.stacktrace, 0x30)
		self.assertEqual(load1.class_name, 'Kenny')
		self.assertIn(2, self.hf.classloads_by_id)
		self.assertIs(self.hf.classloads_by_id[2], load1)

		self.assertIn(0x97104329, self.hf.classloads)
		load2 = self.hf.classloads[0x97104329]
		self.assertIsInstance(load2, hprof._parsing.ClassLoad)
		self.assertEqual(load2.class_id, self.id(0x2021222324))
		self.assertEqual(load2.stacktrace, 0x03)
		self.assertEqual(load2.class_name, 'Hamburger')
		self.assertIn(self.id(0x2021222324), self.hf.classloads_by_id)
		self.assertIs(self.hf.classloads_by_id[self.id(0x2021222324)], load2)

		hprof._parsing._resolve_references(self.hf, None)
		self.assertIs(load1.stacktrace, self.dummytrace2)
		self.assertIs(load2.stacktrace, self.dummytrace1)

	def test_duplicate_serial(self):
		self.addload(0x1, 0x2, 0x3, 0xdeadd00d)
		with self.assertRaisesRegex(hprof.error.FormatError, 'duplicate class load serial'):
			self.addload(0x1, 0x200, 0x30, 0xdeadbeef)

	def test_duplicate_objid(self):
		self.addload(0x1, 0x2, 0x3, 0xdeadd00d)
		with self.assertRaisesRegex(hprof.error.FormatError, 'duplicate class load id'):
			self.addload(0x10, 0x2, 0x30, 0xdeadbeef)

	def test_duplicated_objid_equal(self):
		# this situation exists in perler.hprof...
		self.addload(1, 0x2, 0x3, 0xdeadd00d)
		self.addload(6, 0x2, 0x3, 0xdeadd00d)
		self.assertIs(self.hf.classloads[1], self.hf.classloads[6])
		self.assertEqual(self.hf.classloads[1].class_id, 2)
		self.assertEqual(self.hf.classloads[1].stacktrace, 3)
		self.assertEqual(self.hf.classloads[1].class_name, 'Kenny')
		hprof._parsing._resolve_references(self.hf, None)
		self.assertIs(self.hf.classloads[1].stacktrace, self.dummytrace1)

	def test_missing_stacktrace(self):
		self.addload(1, 2, 33, 0xdeadd00d)
		with self.assertRaisesRegex(hprof.error.FormatError, r'stacktrace.*cannot be found'):
			hprof._parsing._resolve_references(self.hf, None)

	def test_eq(self):
		a = hprof._parsing.ClassLoad()
		b = hprof._parsing.ClassLoad()
		self.assertNotEqual(a, b)
		self.assertNotEqual(b, a)
		a.class_id = 7
		b.class_id = 7
		a.stacktrace = 9
		b.stacktrace = 9
		self.assertNotEqual(a, b) # everything needs to be set.
		self.assertNotEqual(b, a)
		a.class_name = 'hello'
		b.class_name = 'hola'
		self.assertNotEqual(a, b)
		self.assertNotEqual(b, a)
		a.class_name = 'hola'
		self.assertEqual(a, b)
		self.assertEqual(b, a)
		a.class_id = 9
		self.assertNotEqual(a, b)
		self.assertNotEqual(b, a)
		b.class_id = 9
		a.stacktrace = 8
		self.assertNotEqual(a, b)
		self.assertNotEqual(b, a)
