#!/usr/bin/env python3
#coding=utf8

from ._slotted import Slotted

class HprofSlice(object, metaclass=Slotted):
	__slots__ = 'hprof_file', 'hprof_addr', '_hproff'

	def __init__(self, hf, addr):
		self.hprof_file = hf
		self.hprof_addr = addr
		if hasattr(type(self), '_hprof_offsets'):
			self._hproff = type(self)._hprof_offsets[self.hprof_file.idsize]

	def __eq__(self, other):
		return self.hprof_addr == other.hprof_addr and self.hprof_file == other.hprof_file and type(self) is type(other)

	def _hprof_utf8(self, offset, nbytes):
		return self.hprof_file.read_utf8(self.hprof_addr + offset, nbytes)

	def _hprof_uint(self, offset):
		return self.hprof_file.read_uint(self.hprof_addr + offset)

	def _hprof_id(self, offset):
		return self.hprof_file.read_id(self.hprof_addr + offset)

	def _hprof_jtype(self, offset):
		return self.hprof_file.read_jtype(self.hprof_addr + offset)

	def _hprof_jvalue(self, offset, jtype):
		return self.hprof_file.read_jvalue(self.hprof_addr + offset, jtype)

	def _hprof_ushort(self, offset):
		return self.hprof_file.read_ushort(self.hprof_addr + offset)
