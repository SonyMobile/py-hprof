import unittest
import hprof

from contextlib import contextmanager
from unittest.mock import MagicMock, sentinel, patch

class TestOpen(unittest.TestCase):

	def test_decompression(self):
		from io import IOBase
		for ext in ('txt', 'txt.bz2', 'txt.gz', 'txt.xz'):
			with self.subTest(ext):
				@contextmanager
				def checkf(hf, f, cb):
					self.assertIs(type(hf), hprof._parsing.HprofFile)
					self.assertIsInstance(f, IOBase)
					self.assertEqual(f.read(), b'Hello World!\n')
					self.assertEqual(f.read(), b'')
					self.assertIs(cb, progress)
					yield
					cleanup()
				for progress in (None, MagicMock()):
					cleanup = MagicMock()
					with patch('hprof._parsing._parse_cm', side_effect=checkf) as mock:
						out = hprof.open('testdata/helloworld.' + ext, progress)
						with out as hf:
							self.assertIs(hf, out)
							self.assertEqual(cleanup.call_count, 0)
						self.assertEqual(cleanup.call_count, 1)
					self.assertEqual(mock.call_count, 1)
					self.assertIs(out, mock.call_args[0][0])
					self.assertTrue(mock.call_args[0][1].closed)
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

@patch('hprof._parsing._parse')
class TestPublicParse(unittest.TestCase):

	def test_parse(self, mock):
		for j in (0, 1):
			for i, (indata, insize) in enumerate(indatas()):
				progress = MagicMock() if j else None
				mock.reset_mock()
				with self.subTest(indata, progresscb=progress):
					out = hprof.parse(indata, progress)
					self.assertEqual(mock.call_count, 1)
					(hf, arg, cb), kwarg = mock.call_args
					self.assertFalse(kwarg)
					self.assertIsInstance(arg, memoryview)
					self.assertEqual(arg, b'Hello World!\n')
					self.assertIs(cb, progress)
					self.assertIs(hf, out)
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
					with hf as tmp:
						self.assertIs(tmp, hf)
						self.assertEqual(arg[0], ord('H'))
					with self.assertRaisesRegex(ValueError, 'released'):
						arg[0]

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
		with patch('hprof._parsing._parse', side_effect=lambda hf, mview, cb: setattr(hf, 'val', mview[1:])):
			with self.assertRaises(BufferError):
				with hprof.open('testdata/helloworld.txt.gz'):
					pass

class TestPrivateParse(unittest.TestCase):

	def test_parse(self):
		indata = 'hello'
		expected = 'abc def'
		progress = MagicMock()
		with patch('hprof._parsing._parse_hprof') as mock:
			hprof._parsing._parse(expected, indata, progress)
		self.assertEqual(mock.call_count, 1)
		self.assertEqual(mock.call_args[0], (expected,indata,progress))
		self.assertFalse(mock.call_args[1])
		self.assertEqual(progress.call_count, 0)

	def test_parse_exc(self):
		indata = 'hello world'
		for exctype in (TypeError, ValueError, KeyError, AttributeError, Exception):
			progress = MagicMock()
			with self.subTest(exctype):
				with patch('hprof._parsing._parse_hprof', side_effect=exctype) as mock:
					with self.assertRaises(hprof.error.UnhandledError):
						hprof._parsing._parse(None, indata, progress)
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
						hprof._parsing._parse(None, indata, progress)
				self.assertEqual(mock.call_count, 1)
				self.assertEqual(progress.call_count, 0)

class TestParseHprof(unittest.TestCase):

	def test_empty_input(self):
		progress = MagicMock()
		hf = sentinel.hf
		with self.assertRaises(hprof.error.UnexpectedEof):
			hprof._parsing._parse_hprof(hf, b'', progress)
		self.assertEqual(progress.call_count, 1)
		self.assertEqual(progress.call_args[0], ('parsing', 0, 0))
		self.assertEqual(progress.call_args[1], {})

	def test_bad_header(self):
		progress = MagicMock()
		hf = sentinel.hf
		with self.assertRaisesRegex(hprof.error.FormatError, r'header.*PROFALE'):
			hprof._parsing._parse_hprof(hf, b'JAVA PROFALE 1.0.1\0\0\0\0\4\0\1\2\3\4\5\6\7', progress)
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
					hprof._parsing._parse_hprof(sentinel.hf, indata[:n], progress)
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
				hf = hprof._parsing.HprofFile()
				hprof._parsing._parse_hprof(hf, indata, progress)
				self.assertCountEqual(hf.unhandled, ())
				self.assertEqual(progress.call_count, 3)
				self.assertEqual(progress.call_args_list[0][0], ('parsing', 0, 31))
				self.assertEqual(progress.call_args_list[0][1], {})
				self.assertEqual(progress.call_args_list[1][0], ('parsing', 31, 31))
				self.assertEqual(progress.call_args_list[1][1], {})
				self.assertEqual(progress.call_args_list[2][0], ('resolving stacktraces', None, None))
				self.assertEqual(progress.call_args_list[2][1], {})

	def test_one_record(self):
		for v in (1,2,3):
			with self.subTest('version10%d' % v):
				indata = b'JAVA PROFILE 1.0.%d\0\0\0\0\4\0\1\2\3\4\5\6\7\x50\0\0\0\0\0\0\0\2\x33\x44' % v
				progress = MagicMock()
				hf = hprof._parsing.HprofFile()
				with patch('hprof._parsing.record_parsers', {}), patch('hprof._parsing._resolve_references') as resolve:
					hprof._parsing._parse_hprof(hf, indata, progress)
				self.assertEqual(hf.unhandled, {0x50: 1})
				self.assertEqual(resolve.call_count, 1)
				self.assertEqual(resolve.call_args[0], (hf,progress))
				self.assertFalse(resolve.call_args[1])
				self.assertEqual(progress.call_count, 3)
				self.assertEqual(progress.call_args_list[0][0], ('parsing', 0, 42))
				self.assertEqual(progress.call_args_list[0][1], {})
				self.assertEqual(progress.call_args_list[1][0], ('parsing', 32, 42))
				self.assertEqual(progress.call_args_list[1][1], {})
				self.assertEqual(progress.call_args_list[2][0], ('parsing', 42, 42))
				self.assertEqual(progress.call_args_list[2][1], {})

	def test_one_record_no_progress(self):
		indata = b'JAVA PROFILE 1.0.1\0\0\0\0\4\0\1\2\3\4\5\6\7\x50\0\0\0\0\0\0\0\2\x33\x44'
		mock_parsers = { 0x50: unittest.mock.MagicMock() }
		hf = sentinel.hf
		with patch('hprof._parsing.record_parsers', mock_parsers), patch('hprof._parsing._resolve_references') as resolve, patch('hprof._parsing._instantiate') as instantiate:
			hprof._parsing._parse_hprof(sentinel.hf, indata, None)
		self.assertEqual(mock_parsers[0x50].call_count, 1)
		self.assertIs(mock_parsers[0x50].call_args[0][0], hf)
		self.assertIsInstance(mock_parsers[0x50].call_args[0][1], hprof._parsing.PrimitiveReader)
		self.assertIsNone(mock_parsers[0x50].call_args[0][2])
		self.assertEqual(resolve.call_count, 1)
		self.assertEqual(resolve.call_args[0], (hf,None))
		self.assertFalse(resolve.call_args[1])
		self.assertEqual(instantiate.call_count, 1)
		self.assertEqual(instantiate.call_args[0], (hf,None))
		self.assertFalse(instantiate.call_args[1])

	def test_four_records(self):
		indata = b'JAVA PROFILE 1.0.1\0\5\0\0\5\0\1\2\3\4\5\6\7'
		indata += b'\x50\0\0\0\0\0\0\0\5\x33\x44\x55\x66\x77'
		indata += b'\x01\0\0\0\0\0\0\0\2\x45\x46'
		indata += b'\x50\0\0\0\0\0\0\0\2\x30\x31'
		indata += b'\x02\0\0\0\0\0\0\0\3\x33\x44\x32'
		mock_parsers = {
			0x50: unittest.mock.MagicMock(side_effect=lambda h,r,p: p(50000)),
			0x01: unittest.mock.MagicMock(side_effect=lambda h,r,p: p( 1000)),
		}
		progress = MagicMock()
		hf = hprof._parsing.HprofFile()
		with patch('hprof._parsing.record_parsers', mock_parsers), patch('hprof._parsing._resolve_references') as resolve:
			hprof._parsing._parse_hprof(hf, indata, progress)

		self.assertEqual(mock_parsers[0x50].call_count, 2)
		self.assertEqual(mock_parsers[0x01].call_count, 1)

		self.assertEqual(hf.unhandled, {0x02: 1})
		self.assertEqual(resolve.call_count, 1)
		self.assertEqual(resolve.call_args[0], (hf,progress))
		self.assertFalse(resolve.call_args[1])

		self.assertEqual(progress.call_count, 6)
		self.assertEqual(progress.call_args_list[0][0], ('parsing', 0, 79))
		self.assertEqual(progress.call_args_list[0][1], {})
		self.assertEqual(progress.call_args_list[1][0], ('parsing', 32, 79))
		self.assertEqual(progress.call_args_list[1][1], {})
		self.assertEqual(progress.call_args_list[2][0], ('parsing', 50032, 79))
		self.assertEqual(progress.call_args_list[2][1], {})
		self.assertEqual(progress.call_args_list[3][0], ('parsing',  1046, 79))
		self.assertEqual(progress.call_args_list[3][1], {})
		self.assertEqual(progress.call_args_list[4][0], ('parsing', 50057, 79))
		self.assertEqual(progress.call_args_list[4][1], {})
		self.assertEqual(progress.call_args_list[5][0], ('parsing', 79, 79))
		self.assertEqual(progress.call_args_list[5][1], {})

		for mock in mock_parsers.values():
			for args, kwargs in mock.call_args_list:
				self.assertFalse(kwargs)
				self.assertEqual(len(args), 3)
				self.assertIs(args[0], hf)
				self.assertIsInstance(args[1], hprof._parsing.PrimitiveReader)
				self.assertIsNot(args[2], progress)

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

class TestInstantiate(unittest.TestCase):
	def test_instantiates_one_heap(self):
		hf = MagicMock(_pending_heap=None)
		heap1 = MagicMock()
		hf.heaps = [heap1]
		with patch('hprof._heap_parsing.create_primarrays') as prims, patch('hprof._heap_parsing.create_objarrays') as oarrs:
			hprof._parsing._instantiate(hf, None)
		with self.subTest('primarray'):
			self.assertEqual(prims.call_count, 1)
			self.assertEqual(prims.call_args[1], {})
			self.assertEqual(len(prims.call_args[0]), 1)
			self.assertIs(prims.call_args[0][0], heap1)
		with self.subTest('objarray'):
			self.assertEqual(oarrs.call_count, 1)
			self.assertEqual(oarrs.call_args[1], {})
			self.assertEqual(len(oarrs.call_args[0]), 1)
			self.assertIs(oarrs.call_args[0][0], heap1)

	def test_instantiates_three_heaps(self):
		callback = MagicMock()
		heap1 = MagicMock()
		heap1.__len__.return_value = 20
		heap2 = MagicMock()
		heap2.__len__.return_value = 10
		heap3 = MagicMock()
		heap3.__len__.return_value = 30
		hf = MagicMock(_pending_heap=None)
		hf.heaps = [heap1, heap2, heap3]
		with patch('hprof._heap_parsing.create_primarrays') as prims, patch('hprof._heap_parsing.create_objarrays') as oarrs:
			hprof._parsing._instantiate(hf, callback)

		with self.subTest('primarray'):
			self.assertEqual(prims.call_count, 3)

			self.assertEqual(prims.call_args_list[0][1], {})
			self.assertEqual(len(prims.call_args_list[0][0]), 1)
			self.assertIs(prims.call_args_list[0][0][0], heap1)

			self.assertEqual(prims.call_args_list[1][1], {})
			self.assertEqual(len(prims.call_args_list[1][0]), 1)
			self.assertIs(prims.call_args_list[1][0][0], heap2)

			self.assertEqual(prims.call_args_list[2][1], {})
			self.assertEqual(len(prims.call_args_list[2][0]), 1)
			self.assertIs(prims.call_args_list[2][0][0], heap3)

		with self.subTest('objarray'):
			self.assertEqual(oarrs.call_count, 3)

			self.assertEqual(oarrs.call_args_list[0][1], {})
			self.assertEqual(len(oarrs.call_args_list[0][0]), 1)
			self.assertIs(oarrs.call_args_list[0][0][0], heap1)

			self.assertEqual(oarrs.call_args_list[1][1], {})
			self.assertEqual(len(oarrs.call_args_list[1][0]), 1)
			self.assertIs(oarrs.call_args_list[1][0][0], heap2)

			self.assertEqual(oarrs.call_args_list[2][1], {})
			self.assertEqual(len(oarrs.call_args_list[2][0]), 1)
			self.assertIs(oarrs.call_args_list[2][0][0], heap3)

		with self.subTest('progress'):
			self.assertEqual(callback.call_count, 3)
			self.assertEqual(callback.call_args_list[0][0], ('instantiating heap 1/3', None, None))
			self.assertEqual(callback.call_args_list[1][0], ('instantiating heap 2/3', None, None))
			self.assertEqual(callback.call_args_list[2][0], ('instantiating heap 3/3', None, None))

class TestResolveReferences(unittest.TestCase):
	def test_resolves_one_heap(self):
		hf = MagicMock(_pending_heap=None)
		heap1 = MagicMock()
		hf.heaps = [heap1]
		with patch('hprof._heap_parsing.resolve_heap_references') as rhr:
			hprof._parsing._resolve_references(hf, None)
			self.assertEqual(rhr.call_count, 1)
			self.assertEqual(rhr.call_args[1], {})
			self.assertEqual(len(rhr.call_args[0]), 2)
			self.assertIs(rhr.call_args[0][0], heap1)
			self.assertIsNone(rhr.call_args[0][1])

	def test_resolves_three_heaps(self):
		callback = MagicMock()
		heap1 = MagicMock()
		heap1.__len__.return_value = 20
		heap2 = MagicMock()
		heap2.__len__.return_value = 10
		heap3 = MagicMock()
		heap3.__len__.return_value = 30
		hf = MagicMock(_pending_heap=None)
		hf.heaps = [heap1, heap2, heap3]
		rhr = MagicMock(side_effect=lambda h,cb: cb(h))
		with patch('hprof._heap_parsing.resolve_heap_references', rhr):
			hprof._parsing._resolve_references(hf, callback)
			self.assertEqual(rhr.call_count, 3)
			self.assertEqual(callback.call_count, 4)

			self.assertEqual(rhr.call_args_list[0][1], {})
			self.assertEqual(len(rhr.call_args_list[0][0]), 2)
			self.assertIs(rhr.call_args_list[0][0][0], heap1)
			self.assertIsNotNone(rhr.call_args_list[0][0][1])

			self.assertEqual(rhr.call_args_list[1][1], {})
			self.assertEqual(len(rhr.call_args_list[1][0]), 2)
			self.assertIs(rhr.call_args_list[1][0][0], heap2)
			self.assertIsNotNone(rhr.call_args_list[1][0][1])

			self.assertEqual(rhr.call_args_list[2][1], {})
			self.assertEqual(len(rhr.call_args_list[2][0]), 2)
			self.assertIs(rhr.call_args_list[2][0][0], heap3)
			self.assertIsNotNone(rhr.call_args_list[2][0][1])

			self.assertEqual(callback.call_args_list[0][0], ('resolving stacktraces', None, None))
			self.assertEqual(callback.call_args_list[1][0], ('resolving heap 1/3', heap1, 20))
			self.assertEqual(callback.call_args_list[2][0], ('resolving heap 2/3', heap2, 10))
			self.assertEqual(callback.call_args_list[3][0], ('resolving heap 3/3', heap3, 30))
