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
	def timestamp(self):
		return self.hf.starttime + self.relative_timestamp

	@property
	def relative_timestamp(self):
		return timedelta(microseconds = self.hf.read_uint(self.addr + 1))

	@property
	def bodylen(self):
		return self.hf.read_uint(self.addr + 5)

	@property
	def bodyaddr(self):
		return self.addr + 9

	def __len__(self):
		return 9 + self.bodylen

class Unhandled(Record):
	pass
