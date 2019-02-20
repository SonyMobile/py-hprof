#!/usr/bin/env python3
#coding=utf8

class Slotted(type):
	''' a metaclass that makes sure that classes have __slots__ set '''
	def __new__(cls, name, bases, cdict):
		if len(bases) > 1:
			raise TypeError('I prefer not to bother with multiple inheritance.')
		if len(bases) > 0 and bases[0] is not object and not isinstance(bases[0], Slotted):
			raise TypeError('superclass does not have Slotted metaclass')
		if '__slots__' not in cdict:
			cdict['__slots__'] = ()
		return type.__new__(cls, name, bases, cdict)
