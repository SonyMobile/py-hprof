#!/usr/bin/env python3
#coding=utf8

from .base import Record

class Utf8(Record):
	def read(self):
		return self.hf.read_utf8(self.bodyaddr, self.bodylen)
