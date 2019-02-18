#!/usr/bin/env python3
#coding=utf8

class _MetaImmutable(type):
	def __new__(cls, name, bases, cdict):
		if len(bases) > 1:
			raise TypeError('I prefer not to bother with multiple inheritance.')
		if '__slots__' not in cdict:
			cdict['__slots__'] = ()
		return type.__new__(cls, name, bases, cdict)

class Immutable(metaclass=_MetaImmutable):
	def __setattr__(self, name, value):
		if name[0] != '_' and hasattr(self, name):
			raise AttributeError('%s is immutable; cannot set %s' % (type(self), name))
		super().__setattr__(name, value)
