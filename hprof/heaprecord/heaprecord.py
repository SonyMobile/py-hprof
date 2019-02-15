#!/usr/bin/env python3
#coding=utf8

from collections import namedtuple

from ..commonrecord import CommonRecord
from ..errors import *

class HeapRecord(CommonRecord):
	@staticmethod
	def create(hf, addr):
		from .roots import UnknownRoot
		tag = hf.read_byte(addr)
		if tag == 0xff:
			return UnknownRoot(hf, addr)
		else:
			raise FileFormatError('unknown HeapDump subrecord tag 0x%02x' % tag)

	@property
	def rawbody(self):
		return self.hf.read_bytes(self.addr+1, len(self)-1)
