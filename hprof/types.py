#!/usr/bin/env python3
#coding=utf8

from enum import Enum, unique

@unique
class JavaType(Enum):
# TODO: object  =  2
	boolean =  4
	char    =  5
	float   =  6
	double  =  7
	byte    =  8
	short   =  9
	int     = 10
	long    = 11

	def size(self):
		return _sizes[self]

	def __str__(self):
		return self.name

_sizes = {
	JavaType.boolean: 1,
	JavaType.char:    2,
	JavaType.float:   4,
	JavaType.double:  8,
	JavaType.byte:    1,
	JavaType.short:   2,
	JavaType.int:     4,
	JavaType.long:    8,
}
