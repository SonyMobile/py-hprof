class Frame(object):
	__slots__ = ('method', 'signature', 'sourcefile', 'classload', 'line')

class Trace(list):
	__slots__ = ('thread', 'frames')
