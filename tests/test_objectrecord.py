from unittest import TestCase

from .util import HprofBuilder, varying_idsize

import hprof

@varying_idsize
class TestObject(TestCase):
	def setUp(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 1234567890)
		hb.name(123, 'com.example.Hello')
		with hb.record(2, 0) as load:
			load.uint(0)
			load.id(0x12345)
			load.uint(0)
			load.id(123)
		with hb.record(28, 0) as dump:
			with dump.subrecord(33) as obj:
				self.id1 = obj.id(0x998877341)
				obj.uint(0x1789)
				self.cls1 = obj.id(0x12345)
				obj.uint(4)
				obj.uint(0x1badd00d)
			with dump.subrecord(33) as obj:
				self.id2 = obj.id(0x198877341)
				obj.uint(0x1779)
				self.cls2 = obj.id(0x12345)
				obj.uint(10)
				obj.uint(0x2badd00d)
				obj.ushort(0x1020)
				obj.uint(0x1)
			with dump.subrecord(32) as cls:
				cls.id(0x12345)
				cls.uint(0)
				cls.id(0)
				cls.id(0)
				cls.id(0)
				cls.id(0)
				cls.id(0)
				cls.id(0)
				cls.uint(0)
				cls.ushort(0)
				cls.ushort(0)
				cls.ushort(0)
		self.addrs, self.data = hb.build()
		hf = hprof.open(bytes(self.data))
		dump, = hf.dumps()
		heap, = dump.heaps()
		self.o, self.p, _ = sorted(heap.objects(), key=lambda r: r.hprof_addr)

	### type-specific fields ###

	def test_object_stacktrace(self):
		pass # TODO: we don't know about stacktraces yet

	def test_object_class(self):
		pass # TODO: we don't know about classes yet

	### generic record fields ###

	def test_object_addr(self):
		first = self.addrs[0] + 52 + 3 * self.idsize
		self.assertEqual(self.o.hprof_addr, first)
		self.assertEqual(self.p.hprof_addr, first + 13 + 2 * self.idsize)

	def test_object_id(self):
		self.assertEqual(self.o.hprof_id, self.id1)
		self.assertEqual(self.p.hprof_id, self.id2)

	def test_object_type(self):
		self.assertIs(type(self.o), hprof.heap.Object)
		self.assertIs(type(self.p), hprof.heap.Object)

	def test_object_len(self):
		self.assertEqual(self.o._hprof_len, 13 + 2 * self.idsize)
		self.assertEqual(self.p._hprof_len, 19 + 2 * self.idsize)

	def test_object_str(self):
		self.assertEqual(str(self.o), 'Hello(id=0x%x)' % self.id1)
		self.assertEqual(str(self.p), 'Hello(id=0x%x)' % self.id2)

	def test_object_repr(self):
		self.assertEqual(repr(self.o), 'Object(class=com.example.Hello, id=0x%x)' % self.id1)
		self.assertEqual(repr(self.p), 'Object(class=com.example.Hello, id=0x%x)' % self.id2)
