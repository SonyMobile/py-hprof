#!/usr/bin/env python3
#coding=utf8

from unittest import TestCase

import hprof

from .util import HprofBuilder, varying_idsize

@varying_idsize
class TestDump(TestCase):
	def setUp(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 12345)
		with hb.record(1, 1) as name:
			heapnameid = name.id(167812)
			name.bytes('heap')
		with hb.record(1, 2) as name:
			mountainid = name.id(861982141)
			name.bytes('mountain')
		with hb.record(28, 0) as dump:
			with dump.subrecord(0x21) as obj:
				obj.id(1)
				obj.uint(91)
				obj.id(83)
				obj.uint(0)
			with dump.subrecord(0xfe) as info:
				info.uint(77)
				info.id(heapnameid)
			with dump.subrecord(0x21) as obj:
				obj.id(2)
				obj.uint(92)
				obj.id(83)
				obj.uint(0)
		with hb.record(28, 0) as dump:
			with dump.subrecord(0x21) as obj:
				obj.id(3)
				obj.uint(93)
				obj.id(83)
				obj.uint(0)
		with hb.record(44, 0) as dumpend:
			pass # no data
		with hb.record(44, 0) as dumpend:
			pass # no data
		with hb.record(28, 0) as dump:
			with dump.subrecord(0xfe) as info:
				info.uint(18671)
				info.id(mountainid)
			with dump.subrecord(0x21) as obj:
				obj.id(4)
				obj.uint(94)
				obj.id(83)
				obj.uint(0)
			with dump.subrecord(0x20) as cls:
				cls.id(5)
				cls.uint(95)
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
			with dump.subrecord(0xfe) as info:
				info.uint(77)
				info.id(heapnameid)
			with dump.subrecord(0x21) as obj:
				obj.id(6)
				obj.uint(96)
				obj.id(83)
				obj.uint(0)
			with dump.subrecord(0xfe) as info:
				info.uint(18671)
				info.id(mountainid)
			with dump.subrecord(0x21) as obj:
				obj.id(7)
				obj.uint(97)
				obj.id(83)
				obj.uint(0)
		addrs, data = hb.build()
		self.hf = hprof.open(bytes(data))

	def test_dump_type(self):
		dumpA, empty, dumpB = self.hf.dumps()
		self.assertIs(type(dumpA), hprof.Dump)
		self.assertIs(type(empty), hprof.Dump)
		self.assertIs(type(dumpB), hprof.Dump)

	def test_heap_type(self):
		for dump in self.hf.dumps():
			for heap in dump.heaps():
				self.assertIs(type(heap), hprof.Heap)

	def test_dump_count(self):
		dumps = self.hf.dumps()
		next(dumps)
		next(dumps)
		next(dumps)
		with self.assertRaises(StopIteration):
			next(dumps)

	def test_dump_a_get_object(self):
		dumpA, _, _ = self.hf.dumps()
		self.assertEqual(dumpA.get_object(1).hprof_id, 1)
		self.assertEqual(dumpA.get_object(2).hprof_id, 2)
		self.assertEqual(dumpA.get_object(3).hprof_id, 3)
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x4'):
			dumpA.get_object(4)
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x5'):
			dumpA.get_object(5)
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x6'):
			dumpA.get_object(6)
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x7'):
			dumpA.get_object(7)
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x8'):
			dumpA.get_object(8)

	def test_dump_empty_get_object(self):
		_, empty, _ = self.hf.dumps()
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x1'):
			empty.get_object(1)
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x2'):
			empty.get_object(2)
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x3'):
			empty.get_object(3)
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x4'):
			empty.get_object(4)
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x5'):
			empty.get_object(5)
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x6'):
			empty.get_object(6)
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x7'):
			empty.get_object(7)
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x8'):
			empty.get_object(8)

	def test_dump_b_get_object(self):
		_, _, dumpB = self.hf.dumps()
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x1'):
			dumpB.get_object(1)
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x2'):
			dumpB.get_object(2)
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x3'):
			dumpB.get_object(3)
		self.assertEqual(dumpB.get_object(4).hprof_id, 4)
		self.assertEqual(dumpB.get_object(5).hprof_id, 5)
		self.assertEqual(dumpB.get_object(6).hprof_id, 6)
		self.assertEqual(dumpB.get_object(7).hprof_id, 7)
		with self.assertRaisesRegex(hprof.RefError, 'object.*id 0x8'):
			dumpB.get_object(8)

	def test_dump_a_get_class(self):
		dumpA, _, _ = self.hf.dumps()
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x1'):
			dumpA.get_class(1)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x2'):
			dumpA.get_class(2)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x3'):
			dumpA.get_class(3)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x4'):
			dumpA.get_class(4)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x5'):
			dumpA.get_class(5)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x6'):
			dumpA.get_class(6)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x7'):
			dumpA.get_class(7)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x8'):
			dumpA.get_class(8)

	def test_dump_empty_get_class(self):
		_, empty, _ = self.hf.dumps()
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x1'):
			empty.get_class(1)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x2'):
			empty.get_class(2)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x3'):
			empty.get_class(3)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x4'):
			empty.get_class(4)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x5'):
			empty.get_class(5)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x6'):
			empty.get_class(6)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x7'):
			empty.get_class(7)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x8'):
			empty.get_class(8)

	def test_dump_b_get_class(self):
		_, _, dumpB = self.hf.dumps()
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x1'):
			dumpB.get_class(1)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x2'):
			dumpB.get_class(2)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x3'):
			dumpB.get_class(3)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x4'):
			dumpB.get_class(4)
		self.assertEqual(dumpB.get_class(5).hprof_id, 5)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x6'):
			dumpB.get_class(6)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x7'):
			dumpB.get_class(7)
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class.*id 0x8'):
			dumpB.get_class(8)

	def test_dump_heaps(self):
		dumpA, empty, dumpB = self.hf.dumps()
		expectedA = (-1, '<unspecified>'), (77, 'heap')
		self.assertCountEqual(((h.type, h.name) for h in dumpA.heaps()), expectedA)
		expectedB = (77, 'heap'), (18671, 'mountain')
		self.assertCountEqual(((h.type, h.name) for h in dumpB.heaps()), expectedB)
		self.assertCountEqual(empty.heaps(), [])

	def test_heapA_undef_objs(self):
		dumpA, _, _ = self.hf.dumps()
		undefA, = (h for h in dumpA.heaps() if h.type == -1)
		obj = undefA.objects()
		self.assertEqual(next(obj).hprof_id, 1)
		with self.assertRaises(StopIteration):
			next(obj)

	def test_heapA_heap_objs(self):
		dumpA, _, _ = self.hf.dumps()
		heapA, = (h for h in dumpA.heaps() if h.type == 77)
		obj = heapA.objects()
		self.assertEqual(next(obj).hprof_id, 2)
		self.assertEqual(next(obj).hprof_id, 3)
		with self.assertRaises(StopIteration):
			next(obj)

	def test_heapB_heap_objs(self):
		_, _, dumpB = self.hf.dumps()
		heapB, = (h for h in dumpB.heaps() if h.type == 77)
		obj = heapB.objects()
		self.assertEqual(next(obj).hprof_id, 6)
		with self.assertRaises(StopIteration):
			next(obj)

	def test_heapB_mountain_objs(self):
		_, _, dumpB = self.hf.dumps()
		mountainB, = (h for h in dumpB.heaps() if h.type == 18671)
		obj = sorted(mountainB.objects(), key=lambda r: r.hprof_addr)
		self.assertEqual(len(obj), 3)
		self.assertEqual(obj[0].hprof_id, 4)
		self.assertEqual(obj[1].hprof_id, 5)
		self.assertEqual(obj[2].hprof_id, 7)

	def test_heap_equality(self):
		dumpA, empty, dumpB = self.hf.dumps()
		undefA, heapA = dumpA.heaps()
		heapB, mountainB = dumpB.heaps()
		self.assertEqual(heapA, heapA)
		self.assertNotEqual(heapA, undefA)
		self.assertNotEqual(heapA, heapB)
		self.assertNotEqual(heapA, mountainB)
		self.assertNotEqual(heapB, heapA)
		self.assertNotEqual(heapB, undefA)
		self.assertEqual(heapB, heapB)
		self.assertNotEqual(heapB, mountainB)
		self.assertNotEqual(undefA, heapA)
		self.assertEqual(undefA, undefA)
		self.assertNotEqual(undefA, heapB)
		self.assertNotEqual(undefA, mountainB)
		self.assertNotEqual(mountainB, heapA)
		self.assertNotEqual(mountainB, undefA)
		self.assertNotEqual(mountainB, heapB)
		self.assertEqual(mountainB, mountainB)

	def test_heap_parent(self):
		for dump in self.hf.dumps():
			for heap in dump.heaps():
				self.assertIs(heap.dump, dump)

	def test_heap_from_obj(self):
		for dump in self.hf.dumps():
			for heap in dump.heaps():
				for obj in heap.objects():
					self.assertIs(obj.hprof_heap, heap)

	def test_heap_str(self):
		dumpA, _, dumpB = self.hf.dumps()
		undefA,    = (h for h in dumpA.heaps() if h.type == -1)
		heapA,     = (h for h in dumpA.heaps() if h.type == 77)
		heapB,     = (h for h in dumpB.heaps() if h.type == 77)
		mountainB, = (h for h in dumpB.heaps() if h.type == 18671)
		self.assertEqual(str(undefA),    'Heap(type=-1, name=<unspecified>)')
		self.assertEqual(str(heapA),     'Heap(type=77, name=heap)')
		self.assertEqual(str(heapB),     'Heap(type=77, name=heap)')
		self.assertEqual(str(mountainB), 'Heap(type=18671, name=mountain)')

@varying_idsize
class TestDumpNames(TestCase):
	def setUp(self):
		self.addrs = self.data = self.hf = None
		self.hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 12345)
		with self.hb.record(1, 0) as r:
			self.yid = r.id(123)
			r.bytes('YourHeap')
		with self.hb.record(1, 0) as r:
			self.mid1 = r.id(456)
			r.bytes('MyHeap')
		with self.hb.record(1, 0) as r:
			self.mid2 = r.id(789)
			r.bytes('MyHeap')

	def open(self):
		self.addrs, self.data = self.hb.build()
		self.hf = hprof.open(bytes(self.data))

	def test_heap_multiple_names(self):
		with self.hb.record(28, 0) as r:
			with r.subrecord(0xfe) as info:
				info.uint(30)
				info.id(self.yid)
			with r.subrecord(0xfe) as info:
				info.uint(30)
				info.id(self.mid1)
		self.open()
		with self.assertRaisesRegex(hprof.FileFormatError, 'multiple.*YourHeap.*MyHeap'):
			dump, = self.hf.dumps()

	def test_heap_multiple_heaps_same_name(self):
		with self.hb.record(28, 0) as r:
			with r.subrecord(0xfe) as info:
				info.uint(30)
				info.id(self.yid)
			with r.subrecord(0xfe) as info:
				info.uint(45)
				info.id(self.yid)
		self.open()
		dump, = self.hf.dumps()
		self.assertCountEqual((h.name for h in dump.heaps()), ('YourHeap', 'YourHeap'))
		self.assertCountEqual((h.type for h in dump.heaps()), (30, 45))

	def test_heap_invalid_name(self):
		with self.hb.record(28, 0) as r:
			with r.subrecord(0xfe) as info:
				info.uint(30)
				info.id(10)
		self.open()
		with self.assertRaisesRegex(hprof.RefError, 'name.*10'):
			dump, = self.hf.dumps()

@varying_idsize
class TestDumpDuplicateIds(TestCase):
	def setUp(self):
		self.addrs = self.data = self.hf = None
		self.hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 12345)
		with self.hb.record(1, 0) as r:
			r.id(1)
			r.bytes('otherheap')
		with self.hb.record(28, 0) as r:
			with r.subrecord(0x21) as obj:
				obj.id(4)
				obj.uint(94)
				obj.id(83)
				obj.uint(0)

	def open(self):
		self.addrs, self.data = self.hb.build()
		self.hf = hprof.open(bytes(self.data))

	def test_duplicate_id_same_heap(self):
		with self.hb.record(28, 0) as r:
			with r.subrecord(0x21) as obj:
				obj.id(4)
				obj.uint(94)
				obj.id(83)
				obj.uint(0)
		self.open()
		with self.assertRaisesRegex(hprof.FileFormatError, 'duplicate.*4'):
			dump, = self.hf.dumps()

	def test_duplicate_id_other_heap(self):
		with self.hb.record(28, 0) as r:
			with r.subrecord(0xfe) as info:
				info.uint(300)
				info.id(1)
			with r.subrecord(0x21) as obj:
				obj.id(4)
				obj.uint(94)
				obj.id(83)
				obj.uint(0)
		self.open()
		with self.assertRaisesRegex(hprof.FileFormatError, 'duplicate.*4'):
			dump, = self.hf.dumps()

	def test_duplicate_id_other_dump(self):
		with self.hb.record(44, 0) as r:
			pass
		with self.hb.record(28, 0) as r:
			with r.subrecord(0x21) as obj:
				obj.id(4)
				obj.uint(94)
				obj.id(83)
				obj.uint(0)
		self.open()
		a, b = self.hf.dumps()
		a, = a.heaps()
		b, = b.heaps()
		a, = a.objects()
		b, = b.objects()
		self.assertNotEqual(a, b)

@varying_idsize
class TestDumpNameAfterDumps(TestCase):
	def setUp(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 12345)
		with hb.record(28, 0) as r:
			with r.subrecord(0xfe) as info:
				info.uint(300)
				info.id(1)
		with hb.record(1, 0) as r:
			r.id(1)
			r.bytes('otherheap')
		addrs, data = hb.build()
		self.hf = hprof.open(bytes(data))

	def test_dump_name_after_dump(self):
		dump, = self.hf.dumps()
		heap, = dump.heaps()
		self.assertEqual(heap.name, 'otherheap')
