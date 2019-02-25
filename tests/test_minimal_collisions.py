from unittest import TestCase

import hprof

def _descendants(cls):
	yield cls
	for sub in cls.__subclasses__():
		yield from _descendants(sub)

class TestMinimalCollisions(TestCase):
	def setUp(self):
		class MockHprof(object):
			idsize = 4
			def read_ushort(self, offset):
				return 0
		self.hf = MockHprof()

	def _check(self, obj, allowed = ()):
		def bad(name):
			name = name.lower()
			if name.startswith('hprof') or name.startswith('_hprof'):
				return False
			elif name.startswith('__') and name.endswith('__'):
				return False
			return True
		self.assertCountEqual(filter(bad, dir(obj)), allowed)

	def test_collisions_none_missed(self):
		already_tested = [ # don't lie!
			hprof.heap.Allocation,
			hprof.heap.Array,
			hprof.heap.ObjectArray,
			hprof.heap.PrimitiveArray,
			hprof.heap.Object,
			hprof.heap.Class,
		]
		self.assertCountEqual(_descendants(hprof.heap.Allocation), already_tested)

	def test_collisions_allocation(self):
		self._check(hprof.heap.Allocation(self.hf, 0))

	def test_collisions_array(self):
		self._check(hprof.heap.Array(self.hf, 0), allowed=('length',))

	def test_collisions_objectarray(self):
		self._check(hprof.heap.ObjectArray(self.hf, 0), allowed=('length',))

	def test_collisions_primitivearray(self):
		self._check(hprof.heap.PrimitiveArray(self.hf, 0), allowed=('length',))

	def test_collisions_object(self):
		self._check(hprof.heap.Object(self.hf, 0))

	def test_collisions_class(self):
		self._check(hprof.heap.Class(self.hf, 0))