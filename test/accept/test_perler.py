import unittest
import hprof

class TestPerlerParsing(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.hf = hprof.open('testdata/perler.hprof.bz2')

	def test_first_record(self):
		first = self.hf.records[0]
		# TODO: update expected type
		self.assertIsInstance(first, hprof.record.Unhandled)
		self.assertEqual(first.tag, 1) # a name record
		# TODO: check actual content

	def test_num_records(self):
		self.assertEqual(len(self.hf.records), 72630)
