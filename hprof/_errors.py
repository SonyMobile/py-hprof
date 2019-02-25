#!/usr/bin/env python3
#coding=utf8


class Error(Exception):
	pass

class FileFormatError(Error):
	pass

class EofError(Error):
	pass

class RefError(Error):
	pass

class ClassNotFoundError(Error):
	pass

class FieldNotFoundError(Error):
	def __init__(self, ftype, name, base_class_name):
		self.type = ftype
		self.name = name
		assert type(base_class_name) is str
		self.hierarchy = [base_class_name]

	def add_class(self, cname):
		self.hierarchy.append(cname)

	def __str__(self):
		classes = ' -> '.join(reversed(self.hierarchy))
		return '%s field "%s" in class hierarchy %s' % (self.type, self.name, classes)
