class Frame(object):
	__slots__ = ('method', 'signature', 'sourcefile', 'class_name', 'line')

class Trace(list):
	__slots__ = ('thread', 'frames')
