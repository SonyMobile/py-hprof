#!/usr/bin/env python3
#coding=utf8

from datetime import timedelta

from ..offset import *
from ..commonrecord import CommonRecord

def _word_groups(b):
	for i in range(0, len(b), 4):
		yield b[i:i+4]

def _hex_groups(b):
	for g in _word_groups(b):
		yield ''.join('%02x' % b for b in g)


offsets = AutoOffsets(0,
	'TAG',     1,
	'TIME',    4,
	'BODYLEN', 4,
	'BODY'
)

class Record(CommonRecord):
	__slots__ = ()

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

	def __str__(self):
		data = self.rawbody
		if len(data) > 40:
			hexdata = ' '.join(_hex_groups(self.rawbody[:32])) + ' ...'
		else:
			hexdata = ' '.join(_hex_groups(self.rawbody))
		return '%s( %s )' % (type(self).__name__, hexdata)


class Unhandled(Record):
	__slots__ = ()
	pass
