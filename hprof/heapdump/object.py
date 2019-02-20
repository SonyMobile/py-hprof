#!/usr/bin/env python3
#coding=utf8

from .._slotted import Slotted

class Object(object, metaclass=Slotted):
	__slots__ = '_object_heap', '_object_record'

	def __init__(self, heap, record):
		self._object_heap = heap
		self._object_record = record

	# TODO: this is where we'll make a nice API where you can read object fields and stuff.

def object_record(obj):
	return obj._object_record

def object_heap(obj):
	return obj._object_heap
