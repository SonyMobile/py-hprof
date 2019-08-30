import unittest

from struct import pack

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
					fn(self, *args, **kwargs)
		return idsize_loop
	for name in cls.__dict__:
		if name.startswith('test_'):
			fn = getattr(cls, name)
			if callable(fn):
				wrapped = wrap(fn)
				wrapped.__name__ = fn.__name__
				setattr(cls, name, wrapped)
	cls.idsize = 4 # just need something for the initial setUp call

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

	def u4(self, val):
		return self.u(val, 4)

	def i4(self, val):
		return self.i(val, 4)

	def id(self, val):
		return self.u(val, self.idsize)
