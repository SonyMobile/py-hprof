import unittest
import hprof

class TestPerlerParsing(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.hf = hprof.open('testdata/perler.hprof.bz2')

	def test_first_record(self):
		pass
		# TODO: check that the first record (a name record) has been added

	def test_num_unhandled(self):
		# TODO: update expected count as more types are handled.
		self.assertEqual(sum(self.hf.unhandled.values()), 72630)
