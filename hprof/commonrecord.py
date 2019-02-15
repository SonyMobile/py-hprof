#!/usr/bin/env python3
#coding=utf8

class CommonRecord(object):
	__slots__ = 'hf', 'addr'

	def __init__(self, hf, addr):
		self.hf = hf
		self.addr = addr

	def __eq__(self, other):
		return self.addr == other.addr and self.hf == other.hf and type(self) is type(other)

	def __setattr__(self, name, value):
		if hasattr(self, name):
			raise AttributeError('records are immutable')
		super().__setattr__(name, value)

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

	def __len__(self):
		raise TypeError()
