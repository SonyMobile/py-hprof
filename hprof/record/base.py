#!/usr/bin/env python3
#coding=utf8

from datetime import timedelta

from ..offset import *
from ..commonrecord import CommonRecord

offsets = AutoOffsets(0,
	'TAG',     1,
	'TIME',    4,
	'BODYLEN', 4,
	'BODY'
)

class Record(CommonRecord):
	@staticmethod
	def create(hf, addr):
		tag = hf.read_byte(addr)
		# TODO: some form of caching here might not be a bad idea.
		rtype = Unhandled
		for candidate in Record.__subclasses__():
			if getattr(candidate, 'TAG', None) == tag:
				rtype = candidate
		return rtype(hf, addr)

	@property
	def rawbody(self):
		return self.hf.read_bytes(self.addr+9, len(self)-9)

	@property
	def timestamp(self):
		return self.hf.starttime + self.relative_timestamp

	@property
	def relative_timestamp(self):
		return timedelta(microseconds = self.hf.read_uint(self.addr + 1))

	def __len__(self):
		return 9 + self.hf.read_uint(self.addr + 5)

class Unhandled(Record):
	pass
