#!/usr/bin/env python3
#coding=utf8

from struct import pack, unpack
from unittest import TestCase

from .util import HprofBuilder, varying_idsize

import hprof


@varying_idsize
class TestClassRecord(TestCase):
	def setUp(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 787878)
		with hb.record(28, 0) as dump:
			with dump.subrecord(32) as cls:
				self.clsid    = cls.id(97812097)
				cls.uint(12344)  # stack trace
				self.superid  = cls.id(1919)
				cls.id(33)       # loader id
				cls.id(34)       # signer id
				cls.id(35)       # protection domain id
				cls.id(0)        # reserved1
				cls.id(0)        # reserved2
				cls.uint(80)     # instance size

				cls.ushort(0)    # constant pool size (TODO: test with non-zero)

				cls.ushort(3)    # static field count
				self.sf0id = cls.id(104)
				cls.byte(4)      # static field 0 type (boolean)
				cls.byte(1)      # static field 0 value
				self.sf1id = cls.id(106)
				cls.byte(5)      # static field 1 type (char)
				cls.ushort(20170)# static field 1 value (今)
				self.sf2id = cls.id(107)
				cls.byte(2)      #static field 2 type (object)
				self.sfobjid = cls.id(0x912018412515)

				cls.ushort(4)    # instance field count (not including inherited fields)
				self.if0id = cls.id(12345)
				cls.byte(8)      # field 0 type (byte)
				self.if1id = cls.id(54321)
				cls.byte(9)      # field 1 type (short)
				self.if2id = cls.id(12346)
				cls.byte(2)      # field 2 type (object)
				self.if3id = cls.id(12347)
				cls.byte(6)      # field 3 type (float)
		addrs, data = hb.build()
		self.hf = hprof.open(bytes(data))
		dump, = self.hf.records()
		self.cls, = dump.records()

	def tearDown(self):
		self.cls = None
		self.hf.close()
		self.hf = None

	### type-specific fields ###

	def test_class_super(self):
		self.assertEqual(self.cls.hprof_super_class_id, self.superid)

	def test_class_instance_size(self):
		self.assertEqual(self.cls.hprof_instance_size, 80)

	def test_class_static_fields(self):
		a, b, c = self.cls.hprof_static_fields()
		self.assertIs(type(a), hprof.heaprecord.StaticFieldRecord)
		self.assertIs(type(b), hprof.heaprecord.StaticFieldRecord)
		self.assertIs(type(c), hprof.heaprecord.StaticFieldRecord)
		self.assertIs(   a.value, True)
		self.assertEqual(b.value, '今')
		self.assertEqual(c.value, self.sfobjid)
		self.assertEqual(str(a), 'StaticFieldRecord(nameid=0x%x, type=boolean, value=True)' % self.sf0id)
		self.assertEqual(str(b), 'StaticFieldRecord(nameid=0x%x, type=char, value=\'今\')' % self.sf1id)
		self.assertEqual(str(c), 'StaticFieldRecord(nameid=0x%x, type=object, value=0x%x)' % (self.sf2id, self.sfobjid))
		self.assertEqual(len(a), self.idsize + 2)
		self.assertEqual(len(b), self.idsize + 3)
		self.assertEqual(len(c), 2 * self.idsize + 1)
		ad = a.decl
		bd = b.decl
		cd = c.decl
		self.assertEqual(ad.nameid, self.sf0id)
		self.assertEqual(bd.nameid, self.sf1id)
		self.assertEqual(cd.nameid, self.sf2id)
		self.assertEqual(ad.type, hprof.JavaType.boolean)
		self.assertEqual(bd.type, hprof.JavaType.char)
		self.assertEqual(cd.type, hprof.JavaType.object)
		self.assertEqual(str(ad), 'FieldDeclRecord(nameid=0x%x, type=boolean)' % self.sf0id)
		self.assertEqual(str(bd), 'FieldDeclRecord(nameid=0x%x, type=char)' % self.sf1id)
		self.assertEqual(str(cd), 'FieldDeclRecord(nameid=0x%x, type=object)' % self.sf2id)
		self.assertEqual(len(ad), self.idsize + 1)
		self.assertEqual(len(bd), self.idsize + 1)
		self.assertEqual(len(cd), self.idsize + 1)

	def test_class_instance_fields(self):
		a, b, c, d = self.cls.hprof_instance_fields()
		self.assertIs(type(a), hprof.heaprecord.FieldDeclRecord)
		self.assertIs(type(b), hprof.heaprecord.FieldDeclRecord)
		self.assertIs(type(c), hprof.heaprecord.FieldDeclRecord)
		self.assertIs(type(d), hprof.heaprecord.FieldDeclRecord)
		self.assertEqual(a.nameid, self.if0id)
		self.assertEqual(b.nameid, self.if1id)
		self.assertEqual(c.nameid, self.if2id)
		self.assertEqual(d.nameid, self.if3id)
		self.assertEqual(a.type, hprof.JavaType.byte)
		self.assertEqual(b.type, hprof.JavaType.short)
		self.assertEqual(c.type, hprof.JavaType.object)
		self.assertEqual(d.type, hprof.JavaType.float)
		self.assertEqual(str(a), 'FieldDeclRecord(nameid=0x%x, type=byte)' % self.if0id)
		self.assertEqual(str(b), 'FieldDeclRecord(nameid=0x%x, type=short)' % self.if1id)
		self.assertEqual(str(c), 'FieldDeclRecord(nameid=0x%x, type=object)' % self.if2id)
		self.assertEqual(str(d), 'FieldDeclRecord(nameid=0x%x, type=float)' % self.if3id)
		self.assertEqual(len(a), 1 + self.idsize)
		self.assertEqual(len(b), 1 + self.idsize)
		self.assertEqual(len(c), 1 + self.idsize)
		self.assertEqual(len(d), 1 + self.idsize)

	def test_class_stacktrace(self): # TODO
		pass

	### generic record fields ###

	def test_class_addr(self):
		self.assertEqual(self.cls.hprof_addr, 40)

	def test_class_id(self):
		self.assertEqual(self.cls.hprof_id, self.clsid)

	def test_class_type(self):
		self.assertIs(type(self.cls), hprof.heaprecord.ClassRecord)

	def test_class_len(self):
		self.assertEqual(len(self.cls), 1 + 24 + self.idsize * 15)

	def test_class_str(self):
		self.assertEqual(str(self.cls), 'ClassRecord(id=0x%0x)' % self.clsid)

@varying_idsize
class TestNoConstantPool(TestCase):
	def setUp(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 787878)
		with hb.record(28, 0) as dump:
			with dump.subrecord(32) as cls:
				self.clsid    = cls.id(97812097)
				cls.uint(12344)  # stack trace
				self.superid  = cls.id(1919)
				cls.id(33)       # loader id
				cls.id(34)       # signer id
				cls.id(35)       # protection domain id
				cls.id(0)        # reserved1
				cls.id(0)        # reserved2
				cls.uint(80)     # instance size

				cls.ushort(1)    # constant pool size

				cls.ushort(3)    # static field count
				self.sf0id = cls.id(104)
				cls.byte(4)      # static field 0 type (boolean)
				cls.byte(1)      # static field 0 value
				self.sf1id = cls.id(106)
				cls.byte(5)      # static field 1 type (char)
				cls.ushort(20170)# static field 1 value (今)
				self.sf2id = cls.id(107)
				cls.byte(2)      #static field 2 type (object)
				self.sfobjid = cls.id(0x912018412515)

				cls.ushort(4)    # instance field count (not including inherited fields)
				self.if0id = cls.id(12345)
				cls.byte(8)      # field 0 type (byte)
				self.if1id = cls.id(54321)
				cls.byte(9)      # field 1 type (short)
				self.if2id = cls.id(12346)
				cls.byte(2)      # field 2 type (object)
				self.if3id = cls.id(12347)
				cls.byte(6)      # field 3 type (float)
		addrs, data = hb.build()
		self.hf = hprof.open(bytes(data))

	def test_no_constant_pool(self): # TODO: support constant pools; remove this test.
		dump, = self.hf.records()
		with self.assertRaisesRegex(hprof.FileFormatError, 'constant pool'):
			cls, = dump.records()
