#!/usr/bin/env python3
#coding=utf8

from collections import namedtuple
from datetime import timedelta

BaseRecord = namedtuple('BaseRecord', 'hf addr')

class Record(BaseRecord):
	@property
	def tag(self):
		return self.hf.read_byte(self.addr)

	@property
	def id(self):
		raise AttributeError('record type %s has no id' % type(self).__name__)

	@property
	def timestamp(self):
		return self.hf.starttime + self.relative_timestamp

	@property
	def relative_timestamp(self):
		return timedelta(microseconds = self.hf.read_uint(self.addr + 1))

	@property
	def rawbody(self):
		return self.hf.read_bytes(self.addr+9, len(self)-9)

	def __len__(self):
		return 9 + self.hf.read_uint(self.addr + 5)

class Unhandled(Record):
	pass
