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

	def __init__(self, msg, base_class_name=None):
		self._msg = msg
		if base_class_name is None:
			self._hierarchy = None
		else:
			self._hierarchy = [base_class_name]

	def _add_class(self, cname):
		self._hierarchy.append(cname)

	def __str__(self):
		if self._hierarchy:
			classes = ' -> '.join(reversed(self._hierarchy))
			return '%s in class hierarchy %s' % (self._msg, classes)
		return self._msg

class UnfamiliarStringError(Error):
	'''Encountered a java.lang.String object with an internal format unfamiliar to py-hprof.'''
