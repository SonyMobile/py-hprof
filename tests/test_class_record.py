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
		hb.name(104, 'sHello')
		hb.name(106, 'sWorld')
		hb.name(107, 'sTwirled')
		hb.name(12345, 'mAway')
		hb.name(54321, 'mGood')
		hb.name(12346, 'mBye')
		hb.name(12347, 'eeee')
		with hb.record(28, 0) as dump:
			with dump.subrecord(32) as cls:
				self.clsid    = cls.id(97812097)
				cls.uint(12344)  # stack trace
				self.superid  = cls.id(0)
				cls.id(33)       # loader id
				cls.id(34)       # signer id
				cls.id(35)       # protection domain id
				cls.id(0)        # reserved1
				cls.id(0)        # reserved2
				cls.uint(80)     # instance size

				cls.ushort(2)    # constant pool size
				cls.short(1)
				cls.byte(10)
				cls.uint(0x1000)
				cls.short(20)
				cls.byte(8)
				cls.byte(99)

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
		dump, = self.hf.dumps()
		heap, = dump.heaps()
		self.cls, = heap.objects()

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
		self.assertEqual(str(a), 'StaticFieldRecord(name=sHello, type=boolean, value=True)')
		self.assertEqual(str(b), 'StaticFieldRecord(name=sWorld, type=char, value=\'今\')')
		self.assertEqual(str(c), 'StaticFieldRecord(name=sTwirled, type=object, value=0x%x)' % (self.sfobjid))
		self.assertEqual(len(a), self.idsize + 2)
		self.assertEqual(len(b), self.idsize + 3)
		self.assertEqual(len(c), 2 * self.idsize + 1)
		ad = a.decl
		bd = b.decl
		cd = c.decl
		self.assertEqual(ad.name, 'sHello')
		self.assertEqual(bd.name, 'sWorld')
		self.assertEqual(cd.name, 'sTwirled')
		self.assertEqual(ad.type, hprof.JavaType.boolean)
		self.assertEqual(bd.type, hprof.JavaType.char)
		self.assertEqual(cd.type, hprof.JavaType.object)
		self.assertEqual(str(ad), 'FieldDeclRecord(name=sHello, type=boolean)')
		self.assertEqual(str(bd), 'FieldDeclRecord(name=sWorld, type=char)')
		self.assertEqual(str(cd), 'FieldDeclRecord(name=sTwirled, type=object)')
		self.assertEqual(len(ad), self.idsize + 1)
		self.assertEqual(len(bd), self.idsize + 1)
		self.assertEqual(len(cd), self.idsize + 1)

	def test_class_instance_fields(self):
		a, b, c, d = self.cls.hprof_instance_fields()
		self.assertIs(type(a), hprof.heaprecord.FieldDeclRecord)
		self.assertIs(type(b), hprof.heaprecord.FieldDeclRecord)
		self.assertIs(type(c), hprof.heaprecord.FieldDeclRecord)
		self.assertIs(type(d), hprof.heaprecord.FieldDeclRecord)
		self.assertEqual(a.name, 'mAway')
		self.assertEqual(b.name, 'mGood')
		self.assertEqual(c.name, 'mBye')
		self.assertEqual(d.name, 'eeee')
		self.assertEqual(a.type, hprof.JavaType.byte)
		self.assertEqual(b.type, hprof.JavaType.short)
		self.assertEqual(c.type, hprof.JavaType.object)
		self.assertEqual(d.type, hprof.JavaType.float)
		self.assertEqual(str(a), 'FieldDeclRecord(name=mAway, type=byte)')
		self.assertEqual(str(b), 'FieldDeclRecord(name=mGood, type=short)')
		self.assertEqual(str(c), 'FieldDeclRecord(name=mBye, type=object)')
		self.assertEqual(str(d), 'FieldDeclRecord(name=eeee, type=float)')
		self.assertEqual(len(a), 1 + self.idsize)
		self.assertEqual(len(b), 1 + self.idsize)
		self.assertEqual(len(c), 1 + self.idsize)
		self.assertEqual(len(d), 1 + self.idsize)

	def test_class_stacktrace(self): # TODO
		pass

	### generic record fields ###

	def test_class_addr(self):
		self.assertEqual(self.cls.hprof_addr, 40 + (9 + self.idsize) * 7 + len('sHellosWorldsTwirledmAwaymGoodmByeeeee'))

	def test_class_id(self):
		self.assertEqual(self.cls.hprof_id, self.clsid)

	def test_class_type(self):
		self.assertIs(type(self.cls), hprof.heaprecord.Class)

	def test_class_len(self):
		self.assertEqual(len(self.cls), 1 + 35 + self.idsize * 15)

	def test_class_str(self):
		self.assertEqual(str(self.cls), 'Class(id=0x%0x)' % self.clsid)

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
