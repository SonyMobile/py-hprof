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

def indatas():
	import gzip
	yield b'Hello World!\n'
	with open('testdata/helloworld.txt', 'rb') as f:
		yield f
	with gzip.open('testdata/helloworld.txt.gz') as f:
		yield f

@patch('hprof._parsing._parse', side_effect=lambda m: bytes(m) + b' out')
class TestPublicParse(unittest.TestCase):

	def test_parse(self, mock):
		for i, indata in enumerate(indatas(), start=1):
			with self.subTest(indata):
				out = hprof.parse(indata)
				self.assertEqual(out, b'Hello World!\n out')
				self.assertEqual(mock.call_count, i)
				(arg,), kwarg = mock.call_args
				self.assertFalse(kwarg)
				self.assertIsInstance(arg, memoryview)

	def test_string_error(self, mock):
		with self.assertRaises(TypeError):
			hprof.parse('Hello String!')

	def test_text_file_error(self, mock):
		with open('testdata/helloworld.txt') as f:
			with self.assertRaises(TypeError):
				hprof.parse(f)

class TestPublicParseErrors(unittest.TestCase):

	def test_bytes(self):
		for errtype in (
				hprof.error.HprofError,
				hprof.error.FormatError,
				hprof.error.UnexpectedEof,
				hprof.error.UnhandledError,
		):
			for indata in indatas():
				with self.subTest((errtype, indata)):
					with patch('hprof._parsing._parse', side_effect=errtype('boo')):
						with self.assertRaises(errtype, msg='boo'):
							hprof.parse(indata)


class TestPrivateParse(unittest.TestCase):

	def test_parse(self):
		indata = 'hello'
		expected = 'abc def'
		with patch('hprof._parsing._parse_hprof', return_value=expected) as mock:
			self.assertEqual(hprof._parsing._parse(indata), expected)
		self.assertEqual(mock.call_count, 1)
		self.assertEqual(mock.call_args[0], (indata,))
		self.assertFalse(mock.call_args[1])

	def test_parse_exc(self):
		indata = 'hello world'
		for exctype in (TypeError, ValueError, KeyError, AttributeError, Exception):
			with self.subTest(exctype):
				with patch('hprof._parsing._parse_hprof', side_effect=exctype) as mock:
					with self.assertRaises(hprof.error.UnhandledError):
						hprof._parsing._parse(indata)
				self.assertEqual(mock.call_count, 1)

	def test_parse_hproferr(self):
		indata = 'something else'
		for exctype in (
				hprof.error.UnhandledError,
				hprof.error.UnexpectedEof,
				hprof.error.HprofError,
				hprof.error.FormatError,
		):
			with self.subTest(exctype):
				with patch('hprof._parsing._parse_hprof', side_effect=exctype) as mock:
					with self.assertRaises(exctype):
						hprof._parsing._parse(indata)
				self.assertEqual(mock.call_count, 1)

class TestParseHprof(unittest.TestCase):

	def test_empty_input(self):
		with self.assertRaises(hprof.error.UnexpectedEof):
			hprof._parsing._parse_hprof(b'')

	def test_bad_header(self):
		with self.assertRaisesRegex(hprof.error.FormatError, r'header.*PROFALE'):
			hprof._parsing._parse_hprof(b'JAVA PROFALE 1.0.1\0\0\0\0\4\0\1\2\3\4\5\6\7')

	def test_truncated_input(self):
		indata = b'JAVA PROFILE 1.0.1\0\0\0\0\4\0\1\2\3\4\5\6\7\x50\0\0\0\0\0\0\0\2\x33\x44'
		for n in range(len(indata)):
			if n == 31:
				continue # indata[:n] is a valid no-record hprof file.
			with self.subTest(n):
				with self.assertRaises(hprof.error.UnexpectedEof):
					hprof._parsing._parse_hprof(indata[:n])

	def test_no_records(self):
		indata = bytearray(b'JAVA PROFILE 1.0.1\0\0\0\0\4\0\1\2\3\4\5\6\7')
		for n in range(18):
			with self.subTest(n):
				indata[22] = n # different idsize
				hf = hprof._parsing._parse_hprof(indata)
				self.assertEqual(hf.idsize, n)

	def test_one_record(self):
		indata = b'JAVA PROFILE 1.0.1\0\0\0\0\4\0\1\2\3\4\5\6\7\x50\0\0\0\0\0\0\0\2\x33\x44'
		with patch('hprof._parsing.record_parsers', {}):
			hf = hprof._parsing._parse_hprof(indata)
		self.assertEqual(hf.idsize, 4)
		self.assertEqual(hf.unhandled, {0x50: 1})

	def test_four_records(self):
		indata = b'JAVA PROFILE 1.0.1\0\5\0\0\5\0\1\2\3\4\5\6\7'
		indata += b'\x50\0\0\0\0\0\0\0\5\x33\x44\x55\x66\x77'
		indata += b'\x01\0\0\0\0\0\0\0\2\x45\x46'
		indata += b'\x50\0\0\0\0\0\0\0\2\x30\x31'
		indata += b'\x02\0\0\0\0\0\0\0\3\x33\x44\x32'
		mock_parsers = {
			0x50: unittest.mock.MagicMock(),
			0x01: unittest.mock.MagicMock(),
		}
		with patch('hprof._parsing.record_parsers', mock_parsers):
			hf = hprof._parsing._parse_hprof(indata)
		self.assertEqual(hf.idsize, 0x5000005)

		self.assertEqual(mock_parsers[0x50].call_count, 2)
		self.assertEqual(mock_parsers[0x01].call_count, 1)
		self.assertEqual(hf.unhandled, {0x02: 1})

		for mock in mock_parsers.values():
			for args, kwargs in mock.call_args_list:
				self.assertFalse(kwargs)
				self.assertEqual(len(args), 2)
				self.assertIs(args[0], hf)

		self.assertEqual(mock_parsers[0x50].call_args_list[0][0][1], b'\x33\x44\x55\x66\x77')
		self.assertEqual(mock_parsers[0x50].call_args_list[1][0][1], b'\x30\x31')
		self.assertEqual(mock_parsers[0x01].call_args_list[0][0][1], b'\x45\x46')


class TestPrimitiveReader(unittest.TestCase):

	def setUp(self):
		self.r = hprof._parsing.PrimitiveReader(b'hi you\0\xc3\x9czx')

	def test_bytes(self):
		self.assertEqual(self.r.bytes(4), b'hi y')
		self.assertEqual(self.r.bytes(5), b'ou\0\xc3\x9c')
		self.assertEqual(self.r.bytes(1), b'z')
		self.assertEqual(self.r.bytes(1), b'x')
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.bytes(1)
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.bytes(2)

	def test_bytes_oob(self):
		self.assertEqual(self.r.bytes(11), b'hi you\0\xc3\x9czx')
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.bytes(2)
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.bytes(1)

	def test_bytes_half_oob(self):
		self.assertEqual(self.r.bytes(8), b'hi you\0\xc3')
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.bytes(4)
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.bytes(7)
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.bytes(7)
		self.assertEqual(self.r.bytes(3), b'\x9czx')

	def test_bytes_all_oob(self):
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.bytes(12)
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.bytes(22)

	def test_bytes_none(self):
		self.assertEqual(self.r.bytes(0), b'')
		self.assertEqual(self.r.bytes(0), b'')
		self.assertEqual(self.r.bytes(5), b'hi yo')
		self.assertEqual(self.r.bytes(0), b'')
		self.assertEqual(self.r.bytes(0), b'')
		self.assertEqual(self.r.bytes(6), b'u\0\xc3\x9czx')
		self.assertEqual(self.r.bytes(0), b'')
		self.assertEqual(self.r.bytes(0), b'')
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.bytes(1)

	def test_ascii(self):
		self.assertEqual(self.r.ascii(), 'hi you')
		self.assertEqual(self.r.bytes(4), b'\xc3\x9czx')

	def test_ascii_later(self):
		self.assertEqual(self.r.bytes(1), b'h')
		self.assertEqual(self.r.ascii(), 'i you')
		self.assertEqual(self.r.bytes(1), b'\xc3')
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.ascii()

	def test_unsigned_4(self):
		self.assertEqual(self.r.u(4), 0x68692079)
		self.assertEqual(self.r.u(4), 0x6f7500c3)
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.u(4)

	def test_unsigned_unaligned(self):
		self.r.bytes(3)
		self.assertEqual(self.r.u(4), 0x796f7500)
		self.assertEqual(self.r.u(4), 0xc39c7a78)
