#!/usr/bin/env python3
#coding=utf8

from .base import Record

class Utf8(Record):
	@property
	def str(self):
		# TODO: these manual offsets will become annoying when handling more complex records.
		# TODO: maybe use slices to make sure records don't read outside their bounds?
		return self.hf.read_utf8(self.bodyaddr + self.hf.idsize, self.bodylen - self.hf.idsize)
