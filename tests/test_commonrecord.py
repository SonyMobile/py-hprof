#!/usr/bin/env python3
#coding=utf8

from unittest import TestCase
from hprof.commonrecord import CommonRecord
from hprof.record import Record
from hprof.heaprecord import HeapRecord

class TestCommonRecord(TestCase):
	def test_commonrecord_no_id(self):
		r = CommonRecord(None, 10)
		with self.assertRaises(AttributeError):
			r.id

	def test_commonrecord_no_len(self):
		r = CommonRecord(None, 10)
		with self.assertRaises(TypeError):
			len(r)

	def test_commonrecord_not_ordered(self):
		r = CommonRecord(None, 10)
		s = CommonRecord(None, 20)
		with self.assertRaises(TypeError):
			r < s
		with self.assertRaises(TypeError):
			r <= s
		with self.assertRaises(TypeError):
			r > s
		with self.assertRaises(TypeError):
			r >= s

	def test_commonrecord_equality(self):
		r = CommonRecord('fileA', 10)
		s = CommonRecord('fileA', 20)
		t = CommonRecord('fileA', 20)
		u = CommonRecord('fileB', 20)
		self.assertNotEqual(r, s)
		self.assertNotEqual(r, t)
		self.assertNotEqual(r, u)
		self.assertNotEqual(s, r)
		self.assertEqual(   s, t)
		self.assertNotEqual(s, u)
		self.assertNotEqual(t, r)
		self.assertEqual(   t, s)
		self.assertNotEqual(t, u)
		self.assertNotEqual(u, r)
		self.assertNotEqual(u, s)
		self.assertNotEqual(u, t)

	def test_commonrecord_immutable(self):
		r = CommonRecord(None, 20)
		with self.assertRaises(AttributeError):
			r.newattribute = 10
		with self.assertRaises(AttributeError):
			r.hf = 'fileC'
		with self.assertRaises(AttributeError):
			r.addr = 70

	def test_commonrecord_str(self):
		class Corporeal(Record):
			__slots__ = ()
			@property
			def rawbody(self):
				return b"I'm a spooky ghost!"
		c = Corporeal('fileC', 800)
		self.assertEqual(str(c), 'Corporeal( 49276d20 61207370 6f6f6b79 2067686f 737421 )')


class TestRecordSubclasses(TestCase):
	def setUp(self):
		class MockHprof(object):
			idsize = 4
			def read_bytes(self, addr, nbytes):
				b = bytearray(i % 256 for i in range(addr, addr+nbytes))
				return bytes(b)
			def read_uint(self, addr):
				return 10
		fileA = MockHprof()
		fileB = MockHprof()
		def recurse_subclasses(cls):
			yield cls
			for sub in cls.__subclasses__():
				yield from recurse_subclasses(sub)
		self.recs = [(
					subcls(fileA, 10),
					subcls(fileA, 20),
					subcls(fileA, 20),
					subcls(fileB, 20)
				) for subcls in recurse_subclasses(CommonRecord)]

	def test_recordsubclasses_immutable(self):
		for t in self.recs:
			for r in t:
				with self.assertRaises(AttributeError, msg='%s (maybe you need __slots__?)' % type(r)):
					r.newattribute = 10
				with self.assertRaises(AttributeError, msg=type(r)):
					r.hf = 'fileC'
				with self.assertRaises(AttributeError, msg=type(r)):
					r.addr = 70

	def test_recordsubclasses_equality(self):
		def msg(r, s):
			return '(%s, %d) == (%s, %d)' % (r.hf, r.addr, s.hf, s.addr)
		flattened = sum(self.recs, tuple())
		for r in flattened:
			for s in flattened:
				if type(r) is type(s) and r.hf == s.hf and r.addr == s.addr:
					self.assertEqual(r, s, msg=msg(r,s))
				else:
					self.assertNotEqual(r, s, msg=msg(r,s))

	def test_recordsubclasses_rawbody(self):
		''' make sure that all Record subclasses have a rawbody property. '''
		for t in self.recs:
			for r in t:
				if isinstance(r, Record):
					try:
						r.rawbody
					except Exception as e:
						raise AssertionError(type(r), e)
