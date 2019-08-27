import hprof
import unittest

class TestUnhandled(unittest.TestCase):

	def test_tag(self):
		self.assertEqual(hprof.record.Unhandled(99).tag, 99)

	def test_no_extra_attrs(self):
		u = hprof.record.Unhandled(8)
		with self.assertRaises(AttributeError):
			u.extra = 7
		self.assertEqual(u.tag, 8)


