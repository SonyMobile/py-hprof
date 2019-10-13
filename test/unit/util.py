import unittest
import hprof._heap_parsing

def fold(val, bytes):
	if val < 0:
		raise ValueError('%d is less than zero' % val)
	folded = 0
	while val != 0:
		folded ^= val
		val >>= 8 * bytes
	mask = (1 << 8 * bytes) - 1
	return folded & mask

def varyingid(cls):
	''' test class decorator that wraps all test functions
	    in subtest loops with different id sizes '''
	def wrap(fn):
		def idsize_loop(self, *args, **kwargs):
			for idsize in (3,4,5):
				with self.subTest(idsize=idsize):
					self.idsize = idsize
					self.setUp()
					self.assertEqual(self.idsize, idsize)
					fn(self, *args, **kwargs)
					self.assertEqual(self.idsize, idsize)
		return idsize_loop
	for name in cls.__dict__:
		if name.startswith('test_'):
			fn = getattr(cls, name)
			if callable(fn):
				wrapped = wrap(fn)
				wrapped.__name__ = fn.__name__
				setattr(cls, name, wrapped)
	def wrap_setup(fn):
		def idsize_setup(self):
			if hasattr(self, 'idsize'):
				import hprof
				self.hf = hprof._parsing.HprofFile()
				fn(self)
		return idsize_setup
	cls.setUp = wrap_setup(cls.setUp)

	def build(self):
		return Builder(self.idsize)
	cls.build = build

	def id(self, val):
		return fold(val, self.idsize)
	cls.id = id

	return cls


class Builder(bytearray):
	def __init__(self, idsize):
		self.idsize = idsize

	def u(self, val, bytes):
		folded = fold(val, bytes)
		bs = folded.to_bytes(bytes, 'big')
		self.extend(bs)
		return self

	def i(self, val, bytes):
		mask = (1 << 8 * bytes) - 1
		return self.u(val & mask, bytes)

	def u1(self, val):
		return self.u(val, 1)

	def u2(self, val):
		return self.u(val, 2)

	def u4(self, val):
		return self.u(val, 4)

	def u8(self, val):
		return self.u(val, 8)

	def i4(self, val):
		return self.i(val, 4)

	def id(self, val):
		return self.u(val, self.idsize)

	def utf8(self, s):
		self.extend(s.encode('utf8'))
		return self

	def add(self, bytelike):
		self.extend(bytelike)
		return self


class HeapRecordTest(unittest.TestCase):
	def setUp(self):
		self.hf = hprof._parsing.HprofFile()
		self.heap = hprof.heap.Heap()
		load = hprof._parsing.ClassLoad()
		load.class_id = self.id(0x0b1ec7)
		load.class_name = 'java.lang.Object'
		self.hf.classloads_by_id[load.class_id] = load

	def doit(self, rtype, data):
		expected_pos = len(data)
		data.extend(b'sentinel')
		reader = hprof._parsing.PrimitiveReader(memoryview(data), self.idsize)
		parser = hprof._heap_parsing.record_parsers[rtype]
		parser(self.hf, self.heap, reader)
		self.assertEqual(reader._pos, expected_pos, 'parser read more or less than expected')
