import unittest
import hprof

class TestPerlerParsing(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.hf = hprof.open('testdata/perler.hprof.bz2')

	def test_name_record_values(self):
		for nameid, expected in (
			(0x7ff7100edd10, '(Ljava/lang/String;I[Ljava/lang/String;[Ljava/lang/String;[I[I)V'),
			(0x7ff71012c2d0, 'initialising'),
			(0x7ff7100be3b0, 'InsertUndo'),
		):
			with self.subTest(nameid):
				self.assertEqual(self.hf.names[nameid], expected)

	def test_name_record_count(self):
		self.assertEqual(len(self.hf.names), 68327)

	def test_num_unhandled(self):
		# TODO: update expected count as more types are handled.
		self.assertEqual(sum(self.hf.unhandled.values()), 4222)
