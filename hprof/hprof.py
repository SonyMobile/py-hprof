#!/usr/bin/env python3
#coding=utf8

from mmap import mmap, MAP_PRIVATE, PROT_READ
import struct

from .binary import BinaryFile, BinaryStream
from .errors import *
from . import record

# Implementation based on the documentation found here:
# https://github.com/unofficial-openjdk/openjdk/blob/60b7a8f8661234c389e247942a0012da30146a57/src/hotspot/share/services/heapDumper.cpp#L58
# Checking WriteFixedHeader() in art/runtime/hprof/hprof.cc was also helpful.

def open(path):
	return HprofFile(path)

class HprofFile(BinaryFile):
	def __init__(self, path):
		BinaryFile.__init__(self, path)
		s = self.stream()

		ident = s.read_bytes(13)
		if ident != b'JAVA PROFILE ':
			raise FileFormatError('bad header: expected JAVA PROFILE, but found %s' % repr(ident))
		version = s.read_ascii()
		if version != '1.0.3':
			raise FileFormatError('bad version: expected 1.0.3, but found %s' % version)

		self.idsize = s.read_uint()
		self.starttime_ms = (s.read_uint() << 32) + s.read_uint()
		self._first_record_addr = s.addr

	def records(self):
		s = self.stream(self._first_record_addr)
		while True:
			start = s.addr
			try:
				tag = s.read_byte()
			except EofError:
				break # alright, everything lined up nicely!
			r = record.Utf8(self, start) # TODO: check the tag to determine which type to create
			s.skip(len(r) - 1) # skip the rest of the record; -1 because we already read the tag.
			yield r

	def stream(self, start_addr=0):
		return HprofStream(self, start_addr)

class HprofStream(BinaryStream):
	def __init__(self, hf, start_addr):
		BinaryStream.__init__(self, hf._data, start_addr)
