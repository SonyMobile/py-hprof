#!/usr/bin/env python3
#coding=utf8

class offset(object):
	__slots__ = 'bytes', 'ids'

	def __init__(self, bytes, ids):
		self.bytes = bytes
		self.ids = ids

	def __setattr__(self, name, value):
		if hasattr(self, name):
			raise AttributeError('offsets are immutable')
		super().__setattr__(name, value)

	def __eq__(self, other):
		if type(other) is offset:
			return self.bytes == other.bytes and self.ids == other.ids
		return self.bytes == other and self.ids == 0

	def __add__(self, other):
		if type(other) is int:
			return type(self)(self.bytes + other, self.ids)
		elif type(other) is offset:
			return type(self)(self.bytes + other.bytes, self.ids + other.ids)
		return NotImplemented

	def __radd__(self, other):
		return self.__add__(other)

	def __sub__(self, other):
		return self + -other

	def __rsub__(self, other):
		return other + -self

	def __neg__(self):
		return offset(-self.bytes, -self.ids)

	def flatten(self, idsize):
		return self.bytes + self.ids * idsize

def idoffset(ids):
	return offset(0, ids)

def byteoffset(bytes):
	return offset(bytes, 0)

class AutoOffsets(object):
	def __init__(self, *args):
		# if we were running python 3.6, we could make use of order-preserved kwargs... :/
		pos = args[0]
		for i in range(1, len(args), 2):
			name = args[i]
			setattr(self, name, pos)
			if i + 1 < len(args):
				pos += args[i+1]
