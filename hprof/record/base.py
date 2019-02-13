#!/usr/bin/env python3
#coding=utf8

from collections import namedtuple

BaseRecord = namedtuple('BaseRecord', 'hf addr')

class Record(BaseRecord):
	@property
	def tag(self):
		return self.hf.read_byte(self.addr)

	@property
	def timestamp_us(self):
		return self.hf.starttime_ms * 1000 + self.hf.read_uint(self.addr + 1)

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
