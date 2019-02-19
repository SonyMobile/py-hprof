#!/usr/bin/env python3
#coding=utf8

from .immutable import Immutable

class CommonRecord(Immutable):
	__slots__ = 'hf', 'addr'

	def __init__(self, hf, addr):
		self.hf = hf
		self.addr = addr

	def __eq__(self, other):
		return self.addr == other.addr and self.hf == other.hf and type(self) is type(other)

	@property
	def tag(self):
		return self.hf.read_byte(self.addr)

	@property
	def id(self):
		raise AttributeError('record type %s has no id' % type(self).__name__)

	def _read_utf8(self, offset, nbytes):
		return self.hf.read_utf8(self.addr + offset, nbytes)

	def _read_uint(self, offset):
		return self.hf.read_uint(self.addr + offset)

	def _read_id(self, offset):
		return self.hf.read_id(self.addr + offset)

	def _read_jtype(self, offset):
		return self.hf.read_jtype(self.addr + offset)

	def _read_jvalue(self, offset, jtype):
		return self.hf.read_jvalue(self.addr + offset, jtype)

	def _read_ushort(self, offset):
		return self.hf.read_ushort(self.addr + offset)
