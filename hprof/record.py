
class Record(object):
	__slots__ = ('tag',)

class Unhandled(Record):
	__slots__ = ('bytes')
	def __init__(self, bytes):
		self.bytes = bytes
