#!/usr/bin/env python3
#coding=utf8

from enum import Enum, unique

@unique
class JavaType(Enum):
	def __init__(self, value, size):
		self._value_ = value
		self._size = size

	object  =  2, None
	boolean =  4, 1
	char    =  5, 2
	float   =  6, 4
	double  =  7, 8
	byte    =  8, 1
	short   =  9, 2
	int     = 10, 4
	long    = 11, 8

	def size(self, idsize):
		s = self._size
		if s is None:
			return idsize
		else:
			return s

	def __str__(self):
		return self.name
