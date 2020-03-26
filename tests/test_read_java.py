# Copyright (C) 2019 Sony Mobile Communications Inc.
# Licensed under the LICENSE

import hprof

from unittest import TestCase

from .util import HprofBuilder, varying_idsize

@varying_idsize
class TestReadJavaValues(TestCase):
	def setUp(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 123)
		with hb.record(255, 0) as r:
			r.uint(0xff000102)
			r.uint(0x03040506)
			r.uint(0x1f070809)
			r.uint(0x0a0b0c0d)
		addrs, data = hb.build()
		self.hf = hprof.open(bytes(data))
		self.start = addrs[0] + 9

	def test_read_jtype(self):
		with self.assertRaises(hprof.EofError):
			self.hf.read_jtype(-1)
		with self.assertRaisesRegex(hprof.FileFormatError, 'JavaType'):
			self.hf.read_jtype(self.start + 0)
		with self.assertRaisesRegex(hprof.FileFormatError, 'JavaType'):
			self.hf.read_jtype(self.start + 1)
		with self.assertRaisesRegex(hprof.FileFormatError, 'JavaType'):
			self.hf.read_jtype(self.start + 2)
		self.assertEqual(self.hf.read_jtype(self.start + 3), hprof.JavaType.object)
		with self.assertRaisesRegex(hprof.FileFormatError, 'JavaType'):
			self.hf.read_jtype(self.start + 4)
		self.assertEqual(self.hf.read_jtype(self.start + 5), hprof.JavaType.boolean)
		self.assertEqual(self.hf.read_jtype(self.start + 6), hprof.JavaType.char)
		self.assertEqual(self.hf.read_jtype(self.start + 7), hprof.JavaType.float)
		with self.assertRaisesRegex(hprof.FileFormatError, 'JavaType'):
			self.hf.read_jtype(self.start + 8)
		self.assertEqual(self.hf.read_jtype(self.start +  9), hprof.JavaType.double)
		self.assertEqual(self.hf.read_jtype(self.start + 10), hprof.JavaType.byte)
		self.assertEqual(self.hf.read_jtype(self.start + 11), hprof.JavaType.short)
		self.assertEqual(self.hf.read_jtype(self.start + 12), hprof.JavaType.int)
		self.assertEqual(self.hf.read_jtype(self.start + 13), hprof.JavaType.long)
		with self.assertRaisesRegex(hprof.FileFormatError, 'JavaType'):
			self.hf.read_jtype(self.start + 14)
		with self.assertRaisesRegex(hprof.FileFormatError, 'JavaType'):
			self.hf.read_jtype(self.start + 15)
		with self.assertRaises(hprof.EofError):
			self.hf.read_jtype(self.start + 16)

	def test_read_boolean(self):
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(-1, hprof.JavaType.boolean)
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(self.start + 16, hprof.JavaType.boolean)
		self.assertEqual(self.hf.read_jvalue(self.start + 1, hprof.JavaType.boolean), False)
		self.assertEqual(self.hf.read_jvalue(self.start + 2, hprof.JavaType.boolean), True)
		for i in range(16):
			if i == 1 or i == 2:
				continue
			with self.assertRaisesRegex(hprof.FileFormatError, 'invalid boolean'):
				self.hf.read_jvalue(self.start + i, hprof.JavaType.boolean)

	def test_read_char(self):
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(-1, hprof.JavaType.char)
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(self.start + 15, hprof.JavaType.char)
		self.assertEqual(self.hf.read_jvalue(self.start +  0, hprof.JavaType.char), '\uff00')
		self.assertEqual(self.hf.read_jvalue(self.start +  1, hprof.JavaType.char), '\u0001')
		self.assertEqual(self.hf.read_jvalue(self.start +  2, hprof.JavaType.char), '\u0102')
		self.assertEqual(self.hf.read_jvalue(self.start +  3, hprof.JavaType.char), '\u0203')
		self.assertEqual(self.hf.read_jvalue(self.start +  4, hprof.JavaType.char), '\u0304')
		self.assertEqual(self.hf.read_jvalue(self.start +  5, hprof.JavaType.char), '\u0405')
		self.assertEqual(self.hf.read_jvalue(self.start +  6, hprof.JavaType.char), '\u0506')
		self.assertEqual(self.hf.read_jvalue(self.start +  7, hprof.JavaType.char), '\u061f')
		self.assertEqual(self.hf.read_jvalue(self.start +  8, hprof.JavaType.char), '\u1f07')
		self.assertEqual(self.hf.read_jvalue(self.start +  9, hprof.JavaType.char), '\u0708')
		self.assertEqual(self.hf.read_jvalue(self.start + 10, hprof.JavaType.char), '\u0809')
		self.assertEqual(self.hf.read_jvalue(self.start + 11, hprof.JavaType.char), '\u090a')
		self.assertEqual(self.hf.read_jvalue(self.start + 12, hprof.JavaType.char), '\u0a0b')
		self.assertEqual(self.hf.read_jvalue(self.start + 13, hprof.JavaType.char), '\u0b0c')
		self.assertEqual(self.hf.read_jvalue(self.start + 14, hprof.JavaType.char), '\u0c0d')

	def test_read_float(self):
		def mkfloat(neg, exp, mantissa):
			assert 0 <= mantissa < 0x800000
			assert 0 <= exp < 255
			assert neg in (0, 1)
			if exp == 0:
				v = mantissa
				exp = 1
			else:
				v = 0x800000 + mantissa
			v *= 2 ** (exp - 127 - 23)
			return -v if neg else v
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(-1, hprof.JavaType.float)
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(self.start + 13, hprof.JavaType.float)
		self.assertEqual(self.hf.read_jvalue(self.start +  0, hprof.JavaType.float), mkfloat(1, 254, 0x000102))
		self.assertEqual(self.hf.read_jvalue(self.start +  1, hprof.JavaType.float), mkfloat(0,   0, 0x010203))
		self.assertEqual(self.hf.read_jvalue(self.start +  2, hprof.JavaType.float), mkfloat(0,   2, 0x020304))
		self.assertEqual(self.hf.read_jvalue(self.start +  3, hprof.JavaType.float), mkfloat(0,   4, 0x030405))
		self.assertEqual(self.hf.read_jvalue(self.start +  4, hprof.JavaType.float), mkfloat(0,   6, 0x040506))
		self.assertEqual(self.hf.read_jvalue(self.start +  5, hprof.JavaType.float), mkfloat(0,   8, 0x05061f))
		self.assertEqual(self.hf.read_jvalue(self.start +  6, hprof.JavaType.float), mkfloat(0,  10, 0x061f07))
		self.assertEqual(self.hf.read_jvalue(self.start +  7, hprof.JavaType.float), mkfloat(0,  12, 0x1f0708))
		self.assertEqual(self.hf.read_jvalue(self.start +  8, hprof.JavaType.float), mkfloat(0,  62, 0x070809))
		self.assertEqual(self.hf.read_jvalue(self.start +  9, hprof.JavaType.float), mkfloat(0,  14, 0x08090a))
		self.assertEqual(self.hf.read_jvalue(self.start + 10, hprof.JavaType.float), mkfloat(0,  16, 0x090a0b))
		self.assertEqual(self.hf.read_jvalue(self.start + 11, hprof.JavaType.float), mkfloat(0,  18, 0x0a0b0c))
		self.assertEqual(self.hf.read_jvalue(self.start + 12, hprof.JavaType.float), mkfloat(0,  20, 0x0b0c0d))

	def test_read_double(self):
		def mkdouble(neg, exp, mantissa):
			assert 0 <= mantissa < (2 ** 52)
			assert 0 <= exp < (2 ** 11)
			assert neg in (0, 1)
			if exp == 0:
				v = mantissa
				exp = 1
			else:
				v = 2 ** 52 + mantissa
			v *= 2 ** (exp - 1023 - 52)
			return -v if neg else v
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(-1, hprof.JavaType.double)
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(self.start + 9, hprof.JavaType.double)
		self.assertEqual(self.hf.read_jvalue(self.start + 0, hprof.JavaType.double), mkdouble(1, 0x7f0, 0x0010203040506))
		self.assertEqual(self.hf.read_jvalue(self.start + 1, hprof.JavaType.double), mkdouble(0, 0x000, 0x102030405061f))
		self.assertEqual(self.hf.read_jvalue(self.start + 2, hprof.JavaType.double), mkdouble(0, 0x010, 0x2030405061f07))
		self.assertEqual(self.hf.read_jvalue(self.start + 3, hprof.JavaType.double), mkdouble(0, 0x020, 0x30405061f0708))
		self.assertEqual(self.hf.read_jvalue(self.start + 4, hprof.JavaType.double), mkdouble(0, 0x030, 0x405061f070809))
		self.assertEqual(self.hf.read_jvalue(self.start + 5, hprof.JavaType.double), mkdouble(0, 0x040, 0x5061f0708090a))
		self.assertEqual(self.hf.read_jvalue(self.start + 6, hprof.JavaType.double), mkdouble(0, 0x050, 0x61f0708090a0b))
		self.assertEqual(self.hf.read_jvalue(self.start + 7, hprof.JavaType.double), mkdouble(0, 0x061, 0xf0708090a0b0c))
		self.assertEqual(self.hf.read_jvalue(self.start + 8, hprof.JavaType.double), mkdouble(0, 0x1f0, 0x708090a0b0c0d))

	def test_read_byte(self):
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(-1, hprof.JavaType.byte)
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(self.start + 16, hprof.JavaType.byte)
		self.assertEqual(self.hf.read_jvalue(self.start +  0, hprof.JavaType.byte), 0xff)
		self.assertEqual(self.hf.read_jvalue(self.start +  1, hprof.JavaType.byte), 0x0)
		self.assertEqual(self.hf.read_jvalue(self.start +  2, hprof.JavaType.byte), 0x1)
		self.assertEqual(self.hf.read_jvalue(self.start +  3, hprof.JavaType.byte), 0x2)
		self.assertEqual(self.hf.read_jvalue(self.start +  4, hprof.JavaType.byte), 0x3)
		self.assertEqual(self.hf.read_jvalue(self.start +  5, hprof.JavaType.byte), 0x4)
		self.assertEqual(self.hf.read_jvalue(self.start +  6, hprof.JavaType.byte), 0x5)
		self.assertEqual(self.hf.read_jvalue(self.start +  7, hprof.JavaType.byte), 0x6)
		self.assertEqual(self.hf.read_jvalue(self.start +  8, hprof.JavaType.byte), 0x1f)
		self.assertEqual(self.hf.read_jvalue(self.start +  9, hprof.JavaType.byte), 0x7)
		self.assertEqual(self.hf.read_jvalue(self.start + 10, hprof.JavaType.byte), 0x8)
		self.assertEqual(self.hf.read_jvalue(self.start + 11, hprof.JavaType.byte), 0x9)
		self.assertEqual(self.hf.read_jvalue(self.start + 12, hprof.JavaType.byte), 0xa)
		self.assertEqual(self.hf.read_jvalue(self.start + 13, hprof.JavaType.byte), 0xb)
		self.assertEqual(self.hf.read_jvalue(self.start + 14, hprof.JavaType.byte), 0xc)
		self.assertEqual(self.hf.read_jvalue(self.start + 15, hprof.JavaType.byte), 0xd)

	def test_read_short(self):
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(-1, hprof.JavaType.short)
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(self.start + 15, hprof.JavaType.short)
		self.assertEqual(self.hf.read_jvalue(self.start +  0, hprof.JavaType.short), -0x100)
		self.assertEqual(self.hf.read_jvalue(self.start +  1, hprof.JavaType.short), 0x01)
		self.assertEqual(self.hf.read_jvalue(self.start +  2, hprof.JavaType.short), 0x0102)
		self.assertEqual(self.hf.read_jvalue(self.start +  3, hprof.JavaType.short), 0x0203)
		self.assertEqual(self.hf.read_jvalue(self.start +  4, hprof.JavaType.short), 0x0304)
		self.assertEqual(self.hf.read_jvalue(self.start +  5, hprof.JavaType.short), 0x0405)
		self.assertEqual(self.hf.read_jvalue(self.start +  6, hprof.JavaType.short), 0x0506)
		self.assertEqual(self.hf.read_jvalue(self.start +  7, hprof.JavaType.short), 0x061f)
		self.assertEqual(self.hf.read_jvalue(self.start +  8, hprof.JavaType.short), 0x1f07)
		self.assertEqual(self.hf.read_jvalue(self.start +  9, hprof.JavaType.short), 0x0708)
		self.assertEqual(self.hf.read_jvalue(self.start + 10, hprof.JavaType.short), 0x0809)
		self.assertEqual(self.hf.read_jvalue(self.start + 11, hprof.JavaType.short), 0x090a)
		self.assertEqual(self.hf.read_jvalue(self.start + 12, hprof.JavaType.short), 0x0a0b)
		self.assertEqual(self.hf.read_jvalue(self.start + 13, hprof.JavaType.short), 0x0b0c)
		self.assertEqual(self.hf.read_jvalue(self.start + 14, hprof.JavaType.short), 0x0c0d)

	def test_read_int(self):
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(-1, hprof.JavaType.int)
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(self.start + 13, hprof.JavaType.int)
		self.assertEqual(self.hf.read_jvalue(self.start +  0, hprof.JavaType.int), -0x00fffefe)
		self.assertEqual(self.hf.read_jvalue(self.start +  1, hprof.JavaType.int), 0x00010203)
		self.assertEqual(self.hf.read_jvalue(self.start +  2, hprof.JavaType.int), 0x01020304)
		self.assertEqual(self.hf.read_jvalue(self.start +  3, hprof.JavaType.int), 0x02030405)
		self.assertEqual(self.hf.read_jvalue(self.start +  4, hprof.JavaType.int), 0x03040506)
		self.assertEqual(self.hf.read_jvalue(self.start +  5, hprof.JavaType.int), 0x0405061f)
		self.assertEqual(self.hf.read_jvalue(self.start +  6, hprof.JavaType.int), 0x05061f07)
		self.assertEqual(self.hf.read_jvalue(self.start +  7, hprof.JavaType.int), 0x061f0708)
		self.assertEqual(self.hf.read_jvalue(self.start +  8, hprof.JavaType.int), 0x1f070809)
		self.assertEqual(self.hf.read_jvalue(self.start +  9, hprof.JavaType.int), 0x0708090a)
		self.assertEqual(self.hf.read_jvalue(self.start + 10, hprof.JavaType.int), 0x08090a0b)
		self.assertEqual(self.hf.read_jvalue(self.start + 11, hprof.JavaType.int), 0x090a0b0c)
		self.assertEqual(self.hf.read_jvalue(self.start + 12, hprof.JavaType.int), 0x0a0b0c0d)

	def test_read_long(self):
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(-1, hprof.JavaType.long)
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(self.start + 9, hprof.JavaType.long)
		self.assertEqual(self.hf.read_jvalue(self.start +  0, hprof.JavaType.long), -0x00fffefdfcfbfafa)
		self.assertEqual(self.hf.read_jvalue(self.start +  1, hprof.JavaType.long), 0x000102030405061f)
		self.assertEqual(self.hf.read_jvalue(self.start +  2, hprof.JavaType.long), 0x0102030405061f07)
		self.assertEqual(self.hf.read_jvalue(self.start +  3, hprof.JavaType.long), 0x02030405061f0708)
		self.assertEqual(self.hf.read_jvalue(self.start +  4, hprof.JavaType.long), 0x030405061f070809)
		self.assertEqual(self.hf.read_jvalue(self.start +  5, hprof.JavaType.long), 0x0405061f0708090a)
		self.assertEqual(self.hf.read_jvalue(self.start +  6, hprof.JavaType.long), 0x05061f0708090a0b)
		self.assertEqual(self.hf.read_jvalue(self.start +  7, hprof.JavaType.long), 0x061f0708090a0b0c)
		self.assertEqual(self.hf.read_jvalue(self.start +  8, hprof.JavaType.long), 0x1f0708090a0b0c0d)

	def test_read_object(self):
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(-1, hprof.JavaType.object)
		with self.assertRaises(hprof.EofError):
			self.hf.read_jvalue(self.start + 17 - self.idsize, hprof.JavaType.object)
		mask = 2 ** (8 * self.idsize) - 1
		bigval = 0xff000102030405061f0708090a0b0c0d
		for i in range(17-self.idsize):
			shifted = bigval >> (128 - 8 * self.idsize - 8 * i)
			expected = mask & shifted
			self.assertEqual(self.hf.read_jvalue(self.start + i, hprof.JavaType.object), expected)

	def test_read_invalid_type(self):
		with self.assertRaisesRegex(hprof.Error, 'JavaType.*1337'):
			self.hf.read_jvalue(0, 1337)
