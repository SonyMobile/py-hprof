import unittest
import hprof

from unittest.mock import MagicMock, patch

class TestOpen(unittest.TestCase):

	def test_decompression(self):
		from io import IOBase
		for ext in ('txt', 'txt.bz2', 'txt.gz', 'txt.xz'):
			with self.subTest(ext):
				expected = object()
				def checkf(f, cb):
					self.assertIsInstance(f, IOBase)
					self.assertEqual(f.read(), b'Hello World!\n')
					self.assertEqual(f.read(), b'')
					self.assertIs(cb, progress)
					return expected
				for progress in (None, MagicMock()):
					with patch('hprof._parsing.parse', side_effect=checkf) as mock:
						# TODO: gotta save the provided file contents.
						out = hprof.open('testdata/helloworld.' + ext, progress)
					self.assertIs(out, expected)
					self.assertEqual(mock.call_count, 1)
				self.assertEqual(progress.call_count, 1)
				self.assertEqual(progress.call_args[0], ('opening', None, None))
				self.assertEqual(progress.call_args[1], {})

def indatas():
	import gzip
	import bz2
	import lzma
	yield b'Hello World!\n', 13
	with open('testdata/helloworld.txt', 'rb') as f:
		yield f, 13
	with gzip.open('testdata/helloworld.txt.gz') as f:
		yield f, 48
	with bz2.open('testdata/helloworld.txt.bz2') as f:
		yield f, 56
	with lzma.open('testdata/helloworld.txt.xz') as f:
		yield f, 72

@patch('hprof._parsing._parse', side_effect=lambda m, cb: bytes(m) + b' out')
class TestPublicParse(unittest.TestCase):

	def test_parse(self, mock):
		for j in (0, 1):
			for i, (indata, insize) in enumerate(indatas()):
				progress = MagicMock() if j else None
				with self.subTest(indata, progresscb=progress):
					out = hprof.parse(indata, progress)
					self.assertEqual(out, b'Hello World!\n out')
					self.assertEqual(mock.call_count, 5*j + i + 1)
					(arg, cb), kwarg = mock.call_args
					self.assertFalse(kwarg)
					self.assertIsInstance(arg, memoryview)
					self.assertIs(cb, progress)
					if progress:
						if i < 2:
							self.assertEqual(progress.call_count, 0)
						else:
							self.assertEqual(progress.call_count, 3)
							self.assertEqual(progress.call_args_list[0][0], ('extracting', 0, insize))
							self.assertEqual(progress.call_args_list[0][1], {})
							self.assertEqual(progress.call_args_list[1][0], ('extracting', insize-1, insize))
							self.assertEqual(progress.call_args_list[1][1], {})
							self.assertEqual(progress.call_args_list[2][0], ('extracting', insize, insize))
							self.assertEqual(progress.call_args_list[2][1], {})

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
			for indata, insize in indatas():
				with self.subTest((errtype, indata)):
					with patch('hprof._parsing._parse', side_effect=errtype('boo')):
						with self.assertRaises(errtype, msg='boo'):
							hprof.parse(indata)

	def test_keep_mview_gz(self):
		import gzip
		with gzip.open('testdata/helloworld.txt.gz', 'rb') as f:
			with patch('hprof._parsing._parse', side_effect=lambda mview, cb: mview[1:]):
				with self.assertRaises(BufferError):
					hprof.parse(f)


class TestPrivateParse(unittest.TestCase):

	def test_parse(self):
		indata = 'hello'
		expected = 'abc def'
		progress = MagicMock()
		with patch('hprof._parsing._parse_hprof', return_value=expected) as mock:
			self.assertEqual(hprof._parsing._parse(indata, progress), expected)
		self.assertEqual(mock.call_count, 1)
		self.assertEqual(mock.call_args[0], (indata,progress))
		self.assertFalse(mock.call_args[1])
		self.assertEqual(progress.call_count, 0)

	def test_parse_exc(self):
		indata = 'hello world'
		for exctype in (TypeError, ValueError, KeyError, AttributeError, Exception):
			progress = MagicMock()
			with self.subTest(exctype):
				with patch('hprof._parsing._parse_hprof', side_effect=exctype) as mock:
					with self.assertRaises(hprof.error.UnhandledError):
						hprof._parsing._parse(indata, progress)
				self.assertEqual(mock.call_count, 1)
				self.assertEqual(progress.call_count, 0)

	def test_parse_hproferr(self):
		indata = 'something else'
		for exctype in (
				hprof.error.UnhandledError,
				hprof.error.UnexpectedEof,
				hprof.error.HprofError,
				hprof.error.FormatError,
		):
			progress = MagicMock()
			with self.subTest(exctype):
				with patch('hprof._parsing._parse_hprof', side_effect=exctype) as mock:
					with self.assertRaises(exctype):
						hprof._parsing._parse(indata, progress)
				self.assertEqual(mock.call_count, 1)
				self.assertEqual(progress.call_count, 0)

class TestParseHprof(unittest.TestCase):

	def test_empty_input(self):
		progress = MagicMock()
		with self.assertRaises(hprof.error.UnexpectedEof):
			hprof._parsing._parse_hprof(b'', progress)
		self.assertEqual(progress.call_count, 1)
		self.assertEqual(progress.call_args[0], ('parsing', 0, 0))
		self.assertEqual(progress.call_args[1], {})

	def test_bad_header(self):
		progress = MagicMock()
		with self.assertRaisesRegex(hprof.error.FormatError, r'header.*PROFALE'):
			hprof._parsing._parse_hprof(b'JAVA PROFALE 1.0.1\0\0\0\0\4\0\1\2\3\4\5\6\7', progress)
		self.assertEqual(progress.call_count, 1)
		self.assertEqual(progress.call_args[0], ('parsing', 0, 31))
		self.assertEqual(progress.call_args[1], {})

	def test_truncated_input(self):
		indata = b'JAVA PROFILE 1.0.1\0\0\0\0\4\0\1\2\3\4\5\6\7\x50\0\0\0\0\0\0\0\2\x33\x44'
		for n in range(len(indata)):
			if n == 31:
				continue # indata[:n] is a valid no-record hprof file.
			with self.subTest(n):
				progress = MagicMock()
				with self.assertRaises(hprof.error.UnexpectedEof):
					hprof._parsing._parse_hprof(indata[:n], progress)
				self.assertEqual(progress.call_count, 1 if n < 31 else 2)
				self.assertEqual(progress.call_args_list[0][0], ('parsing', 0, n))
				self.assertEqual(progress.call_args_list[0][1], {})
				if n > 31:
					self.assertEqual(progress.call_args_list[1][0], ('parsing', 32, n))
					self.assertEqual(progress.call_args_list[1][1], {})

	def test_no_records(self):
		indata = bytearray(b'JAVA PROFILE 1.0.1\0\0\0\0\4\0\1\2\3\4\5\6\7')
		for n in range(18):
			with self.subTest(n):
				progress = MagicMock()
				indata[22] = n # different idsize
				hf = hprof._parsing._parse_hprof(indata, progress)
				self.assertCountEqual(hf.unhandled, ())
				self.assertEqual(progress.call_count, 3)
				self.assertEqual(progress.call_args_list[0][0], ('parsing', 0, 31))
				self.assertEqual(progress.call_args_list[0][1], {})
				self.assertEqual(progress.call_args_list[1][0], ('parsing', 31, 31))
				self.assertEqual(progress.call_args_list[1][1], {})
				self.assertEqual(progress.call_args_list[2][0], ('resolving', None, None))
				self.assertEqual(progress.call_args_list[2][1], {})

	def test_one_record(self):
		indata = b'JAVA PROFILE 1.0.1\0\0\0\0\4\0\1\2\3\4\5\6\7\x50\0\0\0\0\0\0\0\2\x33\x44'
		progress = MagicMock()
		with patch('hprof._parsing.record_parsers', {}), patch('hprof._parsing._resolve_references') as resolve:
			hf = hprof._parsing._parse_hprof(indata, progress)
		self.assertEqual(hf.unhandled, {0x50: 1})
		self.assertEqual(resolve.call_count, 1)
		self.assertCountEqual(resolve.call_args[0], (hf,))
		self.assertFalse(resolve.call_args[1])
		self.assertEqual(progress.call_count, 4)
		self.assertEqual(progress.call_args_list[0][0], ('parsing', 0, 42))
		self.assertEqual(progress.call_args_list[0][1], {})
		self.assertEqual(progress.call_args_list[1][0], ('parsing', 32, 42))
		self.assertEqual(progress.call_args_list[1][1], {})
		self.assertEqual(progress.call_args_list[2][0], ('parsing', 42, 42))
		self.assertEqual(progress.call_args_list[2][1], {})
		self.assertEqual(progress.call_args_list[3][0], ('resolving', None, None))
		self.assertEqual(progress.call_args_list[3][1], {})

	def test_one_record_no_progress(self):
		indata = b'JAVA PROFILE 1.0.1\0\0\0\0\4\0\1\2\3\4\5\6\7\x50\0\0\0\0\0\0\0\2\x33\x44'
		with patch('hprof._parsing.record_parsers', {}), patch('hprof._parsing._resolve_references') as resolve:
			hf = hprof._parsing._parse_hprof(indata, None)
		self.assertEqual(hf.unhandled, {0x50: 1})
		self.assertEqual(resolve.call_count, 1)
		self.assertCountEqual(resolve.call_args[0], (hf,))
		self.assertFalse(resolve.call_args[1])

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
		progress = MagicMock()
		with patch('hprof._parsing.record_parsers', mock_parsers), patch('hprof._parsing._resolve_references') as resolve:
			hf = hprof._parsing._parse_hprof(indata, progress)

		self.assertEqual(mock_parsers[0x50].call_count, 2)
		self.assertEqual(mock_parsers[0x01].call_count, 1)
		self.assertEqual(hf.unhandled, {0x02: 1})
		self.assertEqual(resolve.call_count, 1)
		self.assertCountEqual(resolve.call_args[0], (hf,))
		self.assertFalse(resolve.call_args[1])

		self.assertEqual(progress.call_count, 4)
		self.assertEqual(progress.call_args_list[0][0], ('parsing', 0, 79))
		self.assertEqual(progress.call_args_list[0][1], {})
		self.assertEqual(progress.call_args_list[1][0], ('parsing', 32, 79))
		self.assertEqual(progress.call_args_list[1][1], {})
		self.assertEqual(progress.call_args_list[2][0], ('parsing', 79, 79))
		self.assertEqual(progress.call_args_list[2][1], {})
		self.assertEqual(progress.call_args_list[3][0], ('resolving', None, None))
		self.assertEqual(progress.call_args_list[3][1], {})

		for mock in mock_parsers.values():
			for args, kwargs in mock.call_args_list:
				self.assertFalse(kwargs)
				self.assertEqual(len(args), 3)
				self.assertIs(args[0], hf)
				self.assertIs(args[2], progress)

		self.assertIsInstance(mock_parsers[0x50].call_args_list[0][0][1], hprof._parsing.PrimitiveReader)
		self.assertIsInstance(mock_parsers[0x50].call_args_list[1][0][1], hprof._parsing.PrimitiveReader)
		self.assertIsInstance(mock_parsers[0x01].call_args_list[0][0][1], hprof._parsing.PrimitiveReader)
		self.assertEqual(mock_parsers[0x50].call_args_list[0][0][1]._pos, 0)
		self.assertEqual(mock_parsers[0x50].call_args_list[1][0][1]._pos, 0)
		self.assertEqual(mock_parsers[0x01].call_args_list[0][0][1]._pos, 0)
		self.assertEqual(mock_parsers[0x50].call_args_list[0][0][1]._bytes, b'\x33\x44\x55\x66\x77')
		self.assertEqual(mock_parsers[0x50].call_args_list[1][0][1]._bytes, b'\x30\x31')
		self.assertEqual(mock_parsers[0x01].call_args_list[0][0][1]._bytes, b'\x45\x46')
		self.assertEqual(mock_parsers[0x50].call_args_list[0][0][1]._idsize, 0x5000005)
		self.assertEqual(mock_parsers[0x50].call_args_list[1][0][1]._idsize, 0x5000005)
		self.assertEqual(mock_parsers[0x01].call_args_list[0][0][1]._idsize, 0x5000005)
