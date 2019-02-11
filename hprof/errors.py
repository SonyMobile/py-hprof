#!/usr/bin/env python3
#coding=utf8


class Error(Exception):
	pass

class FileFormatError(Error):
	def __init__(self, msg):
		self.msg = msg

class EofError(Error):
	def __init__(self, addr, length):
		self.addr = addr
		self.length = length

	def __str__(self):
		return 'tried to read at address %d, but file size is %d' % (self.addr, self.length)
