#!/usr/bin/env python3
#coding=utf8

from mmap import mmap, MAP_PRIVATE, PROT_READ
import struct

from .binary import BinaryFile, BinaryStream
from .errors import *

# Implementation based on the documentation found here:
# https://github.com/unofficial-openjdk/openjdk/blob/60b7a8f8661234c389e247942a0012da30146a57/src/hotspot/share/services/heapDumper.cpp#L58
# Checking WriteFixedHeader() in art/runtime/hprof/hprof.cc was also helpful.

def check_eq(expected, actual, info='bad value'):
	if expected != actual:
		msg = '%s: expected %s, but got %s' % (info, repr(expected), repr(actual))
		raise FileFormatError(msg)

def open(path):
	return HprofFile(path)

class HprofFile(BinaryFile):
	def __init__(self, path):
		BinaryFile.__init__(self, path)
		s = Stream(self, 0)
		expected_header = 'JAVA PROFILE 1.0.3'
		check_eq(s.read_ascii(), 'JAVA PROFILE 1.0.3', 'bad header')
		self.idsize = s.read_uint()

	def stream(self, start_addr=0):
		return HprofStream(self, start_addr)

class HprofStream(BinaryStream):
	def __init__(self, hf, start_addr):
		BinaryStream.__init__(self, hf, start_addr)
