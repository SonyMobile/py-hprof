import unittest
import hprof

from unittest.mock import patch

from .util import dehex

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

	def test_keep_mview_gz(self):
		import gzip
		with gzip.open('testdata/helloworld.txt.gz', 'rb') as f:
			with patch('hprof._parsing._parse', side_effect=lambda mview: mview[1:]):
				with self.assertRaises(BufferError):
					hprof.parse(f)


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

		self.assertIsInstance(mock_parsers[0x50].call_args_list[0][0][1], hprof._parsing.PrimitiveReader)
		self.assertIsInstance(mock_parsers[0x50].call_args_list[1][0][1], hprof._parsing.PrimitiveReader)
		self.assertIsInstance(mock_parsers[0x01].call_args_list[0][0][1], hprof._parsing.PrimitiveReader)
		self.assertEqual(mock_parsers[0x50].call_args_list[0][0][1]._pos, 0)
		self.assertEqual(mock_parsers[0x50].call_args_list[1][0][1]._pos, 0)
		self.assertEqual(mock_parsers[0x01].call_args_list[0][0][1]._pos, 0)
		self.assertEqual(mock_parsers[0x50].call_args_list[0][0][1]._bytes, b'\x33\x44\x55\x66\x77')
		self.assertEqual(mock_parsers[0x50].call_args_list[1][0][1]._bytes, b'\x30\x31')
		self.assertEqual(mock_parsers[0x01].call_args_list[0][0][1]._bytes, b'\x45\x46')


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
		self.assertEqual(self.r.bytes(1), b'\x9c')

	def test_ascii_invalid(self):
		r = hprof._parsing.PrimitiveReader(b'abc\xc3\x9czx\0')
		with self.assertRaises(hprof.error.FormatError):
			r.ascii()
		self.assertEqual(r.bytes(4), b'abc\xc3')

	def test_unsigned_4(self):
		self.assertEqual(self.r.u(4), 0x68692079)
		self.assertEqual(self.r.u(4), 0x6f7500c3)
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.u(4)

	def test_unsigned_5(self):
		self.assertEqual(self.r.u(5), 0x686920796f)
		self.assertEqual(self.r.u(5), 0x7500c39c7a)
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.u(5)

	def test_unsigned_unaligned(self):
		self.r.bytes(3)
		self.assertEqual(self.r.u(4), 0x796f7500)
		self.assertEqual(self.r.u(4), 0xc39c7a78)

	def test_signed_3(self):
		self.r.bytes(4)
		self.assertEqual(self.r.i(3), 0x6f7500)
		self.assertEqual(self.r.i(3), 0xc39c7a - 0x1000000)

	def test_signed_unaligned(self):
		self.r.bytes(3)
		self.assertEqual(self.r.i(4), 0x796f7500)
		self.assertEqual(self.r.i(4), 0xc39c7a78 - 0x100000000)

	def test_invalid_utf8_does_not_consume(self):
		r = hprof._parsing.PrimitiveReader(b'abc\xed\x00\xbddef')
		with self.assertRaises(hprof.error.FormatError):
			r.utf8(9)
		self.assertEqual(r.bytes(3), b'abc')

	def test_utf8_oob(self):
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.utf8(20)
		self.assertEqual(self.r.bytes(5), b'hi yo')


class TestMutf8(unittest.TestCase):

	def decode(self, bytes):
		r = hprof._parsing.PrimitiveReader(bytes)
		return r.utf8(len(bytes))

	def test_encoded_null(self):
		self.assertEqual(self.decode(b'\xc0\x80'), '\0')
		self.assertEqual(self.decode(b'hello\xc0\x80world'), 'hello\0world')

	def test_plain_null(self):
		self.assertEqual(self.decode(b'\0'), '\0')
		self.assertEqual(self.decode(b'hello\0world'), 'hello\0world')

	def test_surrogate_pair(self):
		# "🜚" after being run through javac: 0xeda0bd 0xedbc9a
		self.assertEqual(self.decode(b'\xed\xa0\xbd\xed\xbc\x9a'), '🜚')
		self.assertEqual(self.decode(b'g\xed\xa0\xbd\xed\xbc\x9ald'), 'g🜚ld')
		self.assertEqual(self.decode(b'\xed\xa0\xbd\xed\xbc\x9b'), '🜛')
		self.assertEqual(self.decode(b'sil\xed\xa0\xbd\xed\xbc\x9bver'), 'sil🜛ver')

	def test_invalid_surrogate_pair(self):
		with self.assertRaises(hprof.error.FormatError):
			self.decode(b'\xed\x00\xbd\xed\xbc\x9a')
		with self.assertRaises(hprof.error.FormatError):
			self.decode(b'\xed\xa0\x00\xed\xbc\x9a')
		with self.assertRaises(hprof.error.FormatError):
			self.decode(b'\xed\xa0\xbd\x00\xbc\x9a')
		with self.assertRaises(hprof.error.FormatError):
			self.decode(b'\xed\xa0\xbd\xed\x00\x9a')
		with self.assertRaises(hprof.error.FormatError):
			self.decode(b'\xed\xa0\xbd\xed\xbc\x00')

	def test_truncated_surrogate(self):
		for i in range(1,6):
			with self.subTest(i):
				with self.assertRaises(hprof.error.FormatError):
					self.decode(b'\xed\xa0\xbd\xed\xbc'[:i])
				with self.assertRaises(hprof.error.FormatError):
					self.decode(b'g\xed\xa0\xbd\xed\xbc'[:i+1])

	def test_4byte_utf8(self):
		# real utf8!
		self.assertEqual(self.decode(b'\xf0\x9f\x9c\x9a'), '🜚')
		self.assertEqual(self.decode(b'g\xf0\x9f\x9c\x9ald'), 'g🜚ld')
		self.assertEqual(self.decode(b'\xf0\x9f\x9c\x9b'), '🜛')
		self.assertEqual(self.decode(b'sil\xf0\x9f\x9c\x9bver'), 'sil🜛ver')


class TestParseNameRecord(unittest.TestCase):

	def setUp(self):
		self.hf = hprof._parsing.HprofFile()
		self.hf.idsize = 4

	def callit(self, indata):
		reader = hprof._parsing.PrimitiveReader(memoryview(indata))
		hprof._parsing.record_parsers[0x01](self.hf, reader)

	def test_empty_name(self):
		self.callit(b'\x20\x30\x50\x43')
		self.assertIn(0x20305043, self.hf.names)
		self.assertEqual(self.hf.names[0x20305043], '')

	def test_swedish_name(self):
		self.callit(b'\x11\x15\x10\x55' + 'Hälge ÅÄÖsson'.encode('utf8'))
		self.assertIn(0x11151055, self.hf.names)
		self.assertEqual(self.hf.names[0x11151055], 'Hälge ÅÄÖsson')

	def test_japanese_name(self):
		self.callit(b'\x33\x32\x32\x32' + '山下さん'.encode('utf8'))
		self.assertIn(0x33323232, self.hf.names)
		self.assertEqual(self.hf.names[0x33323232], '山下さん')

	def test_4byte_utf8(self):
		self.callit(b'\x04\x14\x24\x34sil\xf0\x9f\x9c\x9bver')
		self.assertIn(0x04142434, self.hf.names)
		self.assertEqual(self.hf.names[0x04142434], 'sil🜛ver')

	def test_collision(self):
		self.callit(b'\x11\x15\x10\x55abc')
		with self.assertRaises(hprof.error.FormatError):
			self.callit(b'\x11\x15\x10\x55def')
		self.assertIn(0x11151055, self.hf.names)
		self.assertEqual(self.hf.names[0x11151055], 'abc')

	def test_multiple(self):
		self.callit(b'\x33\x32\x32\x32' + 'Hälge ÅÄÖsson'.encode('utf8'))
		self.callit(b'\x11\x15\x10\x55' + '山下さん'.encode('utf8'))
		self.assertIn(0x11151055, self.hf.names)
		self.assertIn(0x33323232, self.hf.names)
		self.assertEqual(self.hf.names[0x11151055], '山下さん')
		self.assertEqual(self.hf.names[0x33323232], 'Hälge ÅÄÖsson')


class TestParseStackTraceRecords(unittest.TestCase):

	def setUp(self):
		self.hf = hprof._parsing.HprofFile()
		self.hf.idsize = 4
		self.hf.names[0x80104030] = 'hello'
		self.hf.names[0x55555555] = 'five'
		self.hf.names[0x08070605] = 'dec'
		self.hf.names[0x10] = 'sixteen'
		self.hf.names[0x11] = 'moreThanSixteen'
		self.hf.names[0xdead] = '()V'
		self.hf.names[0xf00d] = '(Ljava/lang/String;)I'

	def addframe(self, indata):
		reader = hprof._parsing.PrimitiveReader(memoryview(indata))
		hprof._parsing.record_parsers[0x04](self.hf, reader)

	def addstack(self, indata):
		reader = hprof._parsing.PrimitiveReader(memoryview(indata))
		hprof._parsing.parse_stack_frame_record(self.hf, reader)

	def test_frame_only(self):
		self.addframe(dehex('02030405 55555555 0000dead 80104030 12345678 00000051'))
		self.assertIn(0x02030405, self.hf.stackframes)
		frame = self.hf.stackframes[0x02030405]
		self.assertIsInstance(frame, hprof.callstack.Frame)
		self.assertEqual(frame.method, 'five')
		self.assertEqual(frame.signature, '()V')
		self.assertEqual(frame.sourcefile, 'hello')
		# TODO: check class (need to handle class load records first)
		self.assertEqual(frame.line, 0x51)

	def test_negative_line(self):
		self.addframe(dehex('02030405 55555555 0000dead 80104030 12345678 fffffffe'))
		self.assertIn(0x02030405, self.hf.stackframes)
		frame = self.hf.stackframes[0x02030405]
		self.assertIsInstance(frame, hprof.callstack.Frame)
		self.assertEqual(frame.method, 'five')
		self.assertEqual(frame.signature, '()V')
		self.assertEqual(frame.sourcefile, 'hello')
		# TODO: check class (need to handle class load records first)
		self.assertEqual(frame.line, -2)

	def test_duplicate_id(self):
		self.addframe(dehex('02030405 55555555 0000dead 80104030 12345678 00000051'))
		with self.assertRaisesRegex(hprof.error.FormatError, 'duplicate'):
			self.addframe(dehex('02030405 55555555 0000dead 80104030 12345678 fffffffe'))

	def test_multiple_frames(self):
		self.addframe(dehex('03030404 80104030 0000f00d 00000011 12345678 ffffffff'))
		self.addframe(dehex('03030407 00000010 55555555 08070605 22345678 00000171'))
		self.assertIn(0x03030404, self.hf.stackframes)
		self.assertIn(0x03030407, self.hf.stackframes)

		frame = self.hf.stackframes[0x03030404]
		self.assertIsInstance(frame, hprof.callstack.Frame)
		self.assertEqual(frame.method, 'hello')
		self.assertEqual(frame.signature, '(Ljava/lang/String;)I')
		self.assertEqual(frame.sourcefile, 'moreThanSixteen')
		self.assertEqual(frame.line, -1)

		frame = self.hf.stackframes[0x03030407]
		self.assertIsInstance(frame, hprof.callstack.Frame)
		self.assertEqual(frame.method, 'sixteen')
		self.assertEqual(frame.signature, 'five')
		self.assertEqual(frame.sourcefile, 'dec')
		self.assertEqual(frame.line, 0x171)
