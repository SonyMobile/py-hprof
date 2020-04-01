# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

import unittest
import hprof

from unittest.mock import MagicMock, sentinel, call

class TestAddSpecial(unittest.TestCase):
	def setUp(self):
		self.hf = MagicMock()
		self.func = MagicMock(side_effect=['a', 'b', 'c'])
		self.hf.heaps = [
			MagicMock(),
			MagicMock(),
			MagicMock(),
		]
		self.str0 = MagicMock(spec=())
		self.str1 = MagicMock(spec=())
		self.str2 = MagicMock(spec=())
		self.hf.heaps[0].classes = {'java.lang.String': [self.str0]}
		self.hf.heaps[1].classes = {'java.lang.Object': sentinel.obj1}
		self.hf.heaps[2].classes = {'java.lang.Object': sentinel.obj2, 'java.lang.String': [self.str1, self.str2]}

	def test_zero_heaps_no_errors(self):
		self.hf.heaps = []
		hprof._special_cases.add(self.hf, 'java.lang.String', 'stuff', self.func)

	def test_one_heap(self):
		self.hf.heaps = self.hf.heaps[:1]
		hprof._special_cases.add(self.hf, 'java.lang.String', 'stuff', self.func)
		self.assertEqual(self.str0.stuff(1, 2, 3), 'a')
		self.func.assert_called_once_with(1, 2, 3)

	def test_three_heaps(self):
		hprof._special_cases.add(self.hf, 'java.lang.String', 'junk', self.func)
		self.assertEqual(self.str0.junk(1), 'a')
		self.assertEqual(self.str1.junk(9), 'b')
		self.assertEqual(self.str2.junk(4, extra=7), 'c')
		self.assertEqual(self.func.call_count, 3)
		self.assertEqual(self.func.call_args_list[0], ((1,), {}))
		self.assertEqual(self.func.call_args_list[1], ((9,), {}))
		self.assertEqual(self.func.call_args_list[2], ((4,), {'extra':7}))

	def test_exception(self):
		raiser = MagicMock(side_effect=Exception)
		hprof._special_cases.add(self.hf, 'java.lang.String', 'things', raiser)
		with self.assertRaises(Exception):
			self.str0.things()

	def test_fallback(self):
		orig   = MagicMock(return_value=12345)
		raiser = MagicMock(side_effect=Exception)
		self.str0.items = orig
		hprof._special_cases.add(self.hf, 'java.lang.String', 'items', raiser)
		self.assertEqual(self.str0.items(11), 12345)
		raiser.assert_called_once_with(11)
		orig.assert_called_once_with(11)

class TestStringToStr(unittest.TestCase):

	def test_android_string(self):
		def mocked(val):
			mockstr = MagicMock(spec=('__str__'), set_spec=('__str__'))
			mockstr.value = val
			mockstr.__str__ = hprof._special_cases._jstr_to_str
			return mockstr
		def check(val, expected):
			with self.subTest(contents=val):
				s = mocked(val)
				self.assertEqual(str(s), expected)
		def fails(val, errtype, ptn=''):
			with self.subTest(contents=val):
				s = mocked(val)
				with self.assertRaisesRegex(errtype, ptn):
					str(s)
		check(b'', '') # empty string, 1-byte-per-char ("compressed")
		check('', '') # empty string, 2-bytes-per-char ("uncompressed")
		check(b'hello world!', 'hello world!') # plain ascii bytes
		check(range(65, 75), 'ABCDEFGHIJ') # plain ascii bytes
		check('hello!', 'hello!') # plain ascii as chars
		check('wörld!', 'wörld!') # surrogate-free UTF-16 chars
		check('\ud83d\udf1a', '🜚') # a lone surrogate pair
		check('g\ud83d\udf1ald', 'g🜚ld') # a wrapped surrogate pair
		check('\ud83d\udf1a\ud83d\udf1b', '🜚🜛') # two surrogate pairs
		check('g\ud83d\udf1ald, sil\ud83d\udf1bvär', 'g🜚ld, sil🜛vär') # mixed
		# but what if a surrogate is missing its partner?
		fails('\ud83d', UnicodeDecodeError)
		fails('g\ud83dld', UnicodeDecodeError)
		fails('\udf1a', UnicodeDecodeError)
		fails('g\udf1ald', UnicodeDecodeError)
		# and if the "value" array is full of floats or something?
		fails([0.1, 0.2, 0.3], TypeError, 'unknown string class layout')
		# ...or a weird mix of values?
		fails([32, 'a'], Exception)
		fails(['a', 32], Exception)
		# and we don't permit latin1, right?
		fails(b'b\xe5t', UnicodeDecodeError) # latin1!
		fails([98, -27, 116], UnicodeDecodeError)

	def test_openjdk_latin1_string(self):
		counter = 0
		def mocked(val):
			nonlocal counter
			mockstr = MagicMock(spec=('__str__'), set_spec=('__str__'))
			mockstr.value = val
			mockstr.LATIN1 = counter
			mockstr.UTF16  = counter + 1
			mockstr.coder  = counter
			counter += 1
			mockstr.__str__ = hprof._special_cases._jstr_to_str
			return mockstr
		def check(val, expected):
			with self.subTest(contents=val):
				s = mocked(val)
				self.assertEqual(str(s), expected)
		def fails(val, errtype, ptn=''):
			with self.subTest(contents=val):
				s = mocked(val)
				with self.assertRaisesRegex(errtype, ptn):
					str(s)
		check(b'', '') # empty string
		check(b'hello world!', 'hello world!') # plain ascii bytes
		check(range(65, 75), 'ABCDEFGHIJ') # plain ascii bytes
		check(b'b\xe5t', 'båt') # latin1!
		check([98, -27, 116], 'båt') # of course, Java bytes are signed.
		# if it looks like OpenJDK, we shouldn't accept any char arrays
		check('', '') # okay, empty ones are fine I guess. :)
		fails('hello!', TypeError, 'class layout')
		# and if the "value" array is full of floats or something?
		fails([0.1, 0.2, 0.3], TypeError, 'unknown string class layout')
		# ...or a weird mix of values?
		fails([32, 'a'], Exception)
		fails(['a', 32], Exception)

	def test_openjdk_utf16_string(self):
		counter = 0
		def mocked(val):
			nonlocal counter
			mockstr = MagicMock(spec=('__str__'), set_spec=('__str__'))
			mockstr.value = val
			mockstr.LATIN1 = counter
			mockstr.UTF16  = counter + 1
			mockstr.coder  = counter + 1
			counter += 1
			mockstr.__str__ = hprof._special_cases._jstr_to_str
			return mockstr
		def check(val, expected):
			with self.subTest(contents=val):
				s = mocked(val)
				self.assertEqual(str(s), expected)
		def fails(val, errtype, ptn=''):
			with self.subTest(contents=val):
				s = mocked(val)
				with self.assertRaisesRegex(errtype, ptn):
					str(s)
		check(b'', '') # empty string
		check(b'hello world!', '敨汬\u206f潷汲Ⅴ') # that's what happens!
		check(range(65, 75), '䉁䑃䙅䡇䩉') # plain ascii bytes
		check(b'w\0\xf6\0r\0l\0d\0!\0', 'wörld!') # surrogate-free UTF-16 chars
		check(b'\x3d\xd8\x1a\xdf', '🜚') # a lone surrogate pair
		check(b'g\0\x3d\xd8\x1a\xdfl\0d\0', 'g🜚ld') # a wrapped surrogate pair
		check(b'\x3d\xd8\x1a\xdf\x3d\xd8\x1b\xdf', '🜚🜛') # two surrogate pairs
		check(b'g\0\x3d\xd8\x1a\xdfl\0d\0,\0 \0s\0i\0l\0\x3d\xd8\x1b\xdfv\0\xe4\0r\0', 'g🜚ld, sil🜛vär') # mixed
		# if it looks like OpenJDK, we shouldn't accept any char arrays
		check('', '') # empty ones are fine
		fails('hello!', TypeError, 'class layout')
		# but what if a surrogate is missing its partner?
		fails(b'\x3d\xd8', UnicodeDecodeError)
		fails(b'g\x3d\xd8ld', UnicodeDecodeError)
		fails(b'\x1a\xdf', UnicodeDecodeError)
		fails(b'g\x1a\xdfld', UnicodeDecodeError)
		# and if the "value" array is full of floats or something?
		fails([0.1, 0.2, 0.3], TypeError, 'unknown string class layout')
		# ...or a weird mix of values?
		fails([32, 'a'], Exception)
		fails(['a', 32], Exception)
		# and truncated values aren't allowed.
		fails(b'a', UnicodeDecodeError, 'truncated')
		fails(b'hello', UnicodeDecodeError, 'truncated')

	def test_openjdk_unknown_encoding(self):
		mockstr = MagicMock(spec=('__str__'), set_spec=('__str__'))
		mockstr.coder = 7
		mockstr.LATIN1 = 0
		mockstr.UTF16  = 1
		mockstr.value = b'mysterious bytes'
		mockstr.__str__ = hprof._special_cases._jstr_to_str
		# let's fail fast if OpenJDK adds another encoding
		with self.assertRaisesRegex(ValueError, 'unknown string class encoding'):
			str(mockstr)

	def test_unknown_string(self):
		mockstr = MagicMock(spec=('__str__'), set_spec=('__str__'))
		mockstr.__str__ = hprof._special_cases._jstr_to_str
		with self.assertRaisesRegex(TypeError, 'unknown string class layout'):
			str(mockstr)
