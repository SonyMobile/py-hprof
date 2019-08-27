import hprof
import unittest

class TestBase(unittest.TestCase):

	def test_no_extra_attrs(self):
		u = hprof.record.Record()
		with self.assertRaises(AttributeError):
			u.extra = 7
