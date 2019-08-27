
class Record(object):
	__slots__ = ()

class Unhandled(Record):
	__slots__ = ('tag')

	def __init__(self, tag):
		self.tag = tag
