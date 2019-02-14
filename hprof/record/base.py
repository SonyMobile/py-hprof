#!/usr/bin/env python3
#coding=utf8

from collections import namedtuple
from datetime import timedelta

from ..offset import *

offsets = AutoOffsets(0,
	'TAG',     1,
	'TIME',    4,
	'BODYLEN', 4,
	'BODY'
)

BaseRecord = namedtuple('BaseRecord', 'hf addr')

def _word_groups(b):
	for i in range(0, len(b), 4):
		yield b[i:i+4]

def _hex_groups(b):
	for g in _word_groups(b):
		yield ''.join('%02x' % b for b in g)

class Record(BaseRecord):
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

	def _read_utf8(self, offset, nbytes):
		return self.hf.read_utf8(self.addr + offset, nbytes)

	def _read_id(self, offset):
		return self.hf.read_id(self.addr + offset)

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
	pass
