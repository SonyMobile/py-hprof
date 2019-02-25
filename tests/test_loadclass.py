from datetime import datetime, timedelta
from struct import pack
from unittest import TestCase

import hprof

from .util import HprofBuilder, varying_idsize

@varying_idsize
class TestLoadClass(TestCase):
	def setUp(self):
		builder = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 0x0168e143f263)
		with builder.record(1, 123) as r:
			r.id(0x04010203) # string id
			r.bytes(b'com.example.MyFancyClass')
		with builder.record(2, 4567) as r:
			r.uint(0x1a2b3)  # class serial
			r.id(0xbadbad)   # class object id
			r.uint(0xf00d)   # stack trace serial
			r.id(0x04010203) # id of class name string
		self.addrs, self.data = builder.build()
		self.f = hprof.open(bytes(self.data))
		self.c = list(self.f.records())[1]

	def tearDown(self):
		self.c = None
		self.f.close()
		self.f = None

	### type-specific fields ###

	def test_loadclass_name(self):
		self.assertEqual(self.c.class_name, 'com.example.MyFancyClass')

	def test_loadclass_stacktrace(self):
		pass # TODO (stack traces not implemented yet)

	def test_loadclass_class(self):
		pass # TODO (class objects not implemented yet)

	### generic record fields ###

	def test_loadclass_addr(self):
		self.assertEqual(self.c.hprof_addr, self.addrs[1])

	def test_loadclass_type(self):
		self.assertIs(type(self.c), hprof.record.ClassLoad)

	def test_loadclass_rawbody(self):
		self.assertEqual(self.c.rawbody, self.data[self.addrs[1] + 9:])

	def test_loadclass_len(self):
		self.assertEqual(self.c._hprof_len, len(self.data) - self.addrs[1])

	def test_loadclass_str(self):
		self.assertEqual(str(self.c), 'ClassLoad(com.example.MyFancyClass)')
