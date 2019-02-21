#!/usr/bin/env python3
#coding=utf8

from ._slotted import Slotted

class HprofSlice(object, metaclass=Slotted):
	__slots__ = 'hf', 'addr', '_off'

	def __init__(self, hf, addr):
		self.hf = hf
		self.addr = addr
		if hasattr(self, '_offsets'):
			self._off = self._offsets[self.hf.idsize]

	def __eq__(self, other):
		return self.addr == other.addr and self.hf == other.hf and type(self) is type(other)

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

class CommonRecord(HprofSlice, metaclass=Slotted):
	@property
	def tag(self):
		return self.hf.read_byte(self.addr)
