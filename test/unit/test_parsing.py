import unittest
import hprof

from unittest.mock import patch

class TestOpen(unittest.TestCase):

	def test_decompression(self):
		from io import IOBase
		for ext in ('txt', 'txt.bz2', 'txt.gz', 'txt.xz'):
			with self.subTest(ext):
				expected = object()
				def checkf(f):
					self.assertIsInstance(f, IOBase)
					self.assertEqual(f.read(), b'Hello World!\n')
					self.assertEqual(f.read(), b'')
					return expected
				with patch('hprof._parsing.parse', side_effect=checkf) as mock:
					# TODO: gotta save the provided file contents.
					out = hprof.open('testdata/helloworld.' + ext)
				self.assertIs(out, expected)
				self.assertEqual(mock.call_count, 1)

@patch('hprof._parsing._parse', side_effect=lambda m: bytes(m) + b' out')
class TestPublicParse(unittest.TestCase):

	def test_bytes(self, mock):
		out = hprof.parse(b'here are some bytes')
		self.assertEqual(out, b'here are some bytes out')
		self.assertEqual(mock.call_count, 1)
		(arg,), _ = mock.call_args
		self.assertIsInstance(arg, memoryview)

	def test_file(self, mock):
		with open('testdata/helloworld.txt', 'rb') as f:
			out = hprof.parse(f)
			self.assertEqual(out, b'Hello World!\n out')
			self.assertEqual(mock.call_count, 1)
			(arg,), _ = mock.call_args
			self.assertIsInstance(arg, memoryview)

	def test_io(self, mock):
		import gzip
		with gzip.open('testdata/helloworld.txt.gz') as f:
			out = hprof.parse(f)
			self.assertEqual(out, b'Hello World!\n out')
			self.assertEqual(mock.call_count, 1)
			(arg,), _ = mock.call_args
			self.assertIsInstance(arg, memoryview)

	def test_string_error(self, mock):
		with self.assertRaises(TypeError):
			hprof.parse('Hello String!')

	def test_text_file_error(self, mock):
		with open('testdata/helloworld.txt') as f:
			with self.assertRaises(TypeError):
				hprof.parse(f)
