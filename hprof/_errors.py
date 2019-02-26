class Error(Exception):
	''' Base Error from hprof. Rarely thrown. '''

class FileFormatError(Error):
	'''Unexpected or unhandled data.'''

class EofError(Error):
	'''Tried to read outside the hprof file data.'''

class RefError(Error):
	'''A lookup by ID or serial failed.'''

class ClassNotFoundError(Error):
	'''A class lookup failed.'''

class FieldNotFoundError(Error):
	'''Tried to read a field that was not found.'''

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
