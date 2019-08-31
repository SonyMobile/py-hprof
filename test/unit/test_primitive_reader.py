import unittest
import hprof

class TestPrimitiveReader(unittest.TestCase):

	def setUp(self):
		self.r = hprof._parsing.PrimitiveReader(b'hi you\0\xc3\x9czx', 4)

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
		r = hprof._parsing.PrimitiveReader(b'abc\xc3\x9czx\0', 4)
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
		r = hprof._parsing.PrimitiveReader(b'abc\xed\x00\xbddef', 4)
		with self.assertRaises(hprof.error.FormatError):
			r.utf8(9)
		self.assertEqual(r.bytes(3), b'abc')

	def test_utf8_oob(self):
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.utf8(20)
		self.assertEqual(self.r.bytes(5), b'hi yo')

	def test_id_size3(self):
		self.r._idsize = 3
		self.assertEqual(self.r.id(), 0x686920)
		self.assertEqual(self.r.id(), 0x796f75)
		self.assertEqual(self.r.id(), 0x00c39c)
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.id()

	def test_id_size4(self):
		self.r._idsize = 4
		self.assertEqual(self.r.id(), 0x68692079)
		self.assertEqual(self.r.id(), 0x6f7500c3)
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.id()

	def test_id_size_5(self):
		self.r._idsize = 5
		self.assertEqual(self.r.id(), 0x686920796f)
		self.assertEqual(self.r.id(), 0x7500c39c7a)
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.id()

	def test_id_size_11(self):
		self.r._idsize = 11
		self.assertEqual(self.r.id(), 0x686920796f7500c39c7a78)
		with self.assertRaises(hprof.error.UnexpectedEof):
			self.r.id()

	def test_jobject(self):
		for idsize, expected in ((3, 0x030405), (4, 0x03040506), (5, 0x0304050607)):
			for t in (bytes, memoryview):
				with self.subTest(t, idsize=idsize):
					r = hprof._parsing.PrimitiveReader(t(b'\2\3\4\5\6\7\10\11'), idsize)
					self.assertIs(r.jtype(), hprof.jtype.object)
					self.assertEqual(r.jval(hprof.jtype.object), expected)

	def test_jboolean(self):
		for t in (bytes, memoryview):
			with self.subTest(t):
				r = hprof._parsing.PrimitiveReader(t(b'\4\1\0\2\0\3\4\xff'), None)
				self.assertIs(r.jtype(), hprof.jtype.boolean)
				self.assertIs(r.jval(hprof.jtype.boolean), True)
				self.assertIs(r.jval(hprof.jtype.boolean), False)
				self.assertIs(r.jval(hprof.jtype.boolean), True)
				self.assertIs(r.jval(hprof.jtype.boolean), False)
				self.assertIs(r.jval(hprof.jtype.boolean), True)
				self.assertIs(r.jval(hprof.jtype.boolean), True)
				self.assertIs(r.jval(hprof.jtype.boolean), True)
				with self.assertRaises(hprof.error.UnexpectedEof):
					r.jval(hprof.jtype.boolean)

	def test_jchar(self):
		for t in (bytes, memoryview):
			with self.subTest(t):
				r = hprof._parsing.PrimitiveReader(t(b'\5\0\x20\0\x61\xd8\x3d\xdf\x1b\xee'), None)
				self.assertIs(r.jtype(), hprof.jtype.char)
				self.assertEqual(r.jval(hprof.jtype.char), ' ')
				self.assertEqual(r.jval(hprof.jtype.char), 'a')
				self.assertEqual(r.jval(hprof.jtype.char), '\ud83d')
				self.assertEqual(r.jval(hprof.jtype.char), '\udf1b')
				with self.assertRaises(hprof.error.UnexpectedEof):
					r.jval(hprof.jtype.char)

	def test_jfloat(self):
		for t in (bytes, memoryview):
			with self.subTest(t):
				r = hprof._parsing.PrimitiveReader(t(b'\6\x3f\x80\x00\x00\x7f\x80\x00\x00\x41\xc0\x00\x40\xee'), None)
				self.assertIs(r.jtype(), hprof.jtype.float)
				self.assertEqual(r.jval(hprof.jtype.float), 1.0)
				self.assertEqual(r.jval(hprof.jtype.float), float('inf'))
				self.assertEqual(r.jval(hprof.jtype.float), 24 + 1 / 8192)
				with self.assertRaises(hprof.error.UnexpectedEof):
					r.jval(hprof.jtype.float)

	def test_jdouble(self):
		for t in (bytes, memoryview):
			with self.subTest(t):
				r = hprof._parsing.PrimitiveReader(t(b'\7\x3f\xf0\x00\x00\x00\x00\x00\x00\xee'), None)
				self.assertIs(r.jtype(), hprof.jtype.double)
				self.assertEqual(r.jval(hprof.jtype.double), 1.0)
				with self.assertRaises(hprof.error.UnexpectedEof):
					r.jval(hprof.jtype.double);

	def test_jbyte(self):
		for t in (bytes, memoryview):
			with self.subTest(t):
				r = hprof._parsing.PrimitiveReader(t(b'\x08\0\x20\0\x61\xd8\x3d\xdf\x1b\xee'), None)
				self.assertIs(r.jtype(), hprof.jtype.byte)
				self.assertEqual(r.jval(hprof.jtype.byte), 0)
				self.assertEqual(r.jval(hprof.jtype.byte), 0x20)
				self.assertEqual(r.jval(hprof.jtype.byte), 0)
				self.assertEqual(r.jval(hprof.jtype.byte), 0x61)
				self.assertEqual(r.jval(hprof.jtype.byte), 0xd8 - 0x100)
				self.assertEqual(r.jval(hprof.jtype.byte), 0x3d)
				self.assertEqual(r.jval(hprof.jtype.byte), 0xdf - 0x100)
				self.assertEqual(r.jval(hprof.jtype.byte), 0x1b)
				self.assertEqual(r.jval(hprof.jtype.byte), 0xee - 0x100)
				with self.assertRaises(hprof.error.UnexpectedEof):
					r.jval(hprof.jtype.byte)

	def test_jshort(self):
		for t in (bytes, memoryview):
			with self.subTest(t):
				r = hprof._parsing.PrimitiveReader(t(b'\x09\0\x20\0\x61\xd8\x3d\xdf\x1b\x0e'), None)
				self.assertIs(r.jtype(), hprof.jtype.short)
				self.assertEqual(r.jval(hprof.jtype.short), 0x20)
				self.assertEqual(r.jval(hprof.jtype.short), 0x61)
				self.assertEqual(r.jval(hprof.jtype.short), 0xd83d - 0x10000)
				self.assertEqual(r.jval(hprof.jtype.short), 0xdf1b - 0x10000)
				with self.assertRaises(hprof.error.UnexpectedEof):
					r.jval(hprof.jtype.short)

	def test_jint(self):
		for t in (bytes, memoryview):
			with self.subTest(t):
				r = hprof._parsing.PrimitiveReader(t(b'\x0a\0\x20\0\x61\xd8\x3d\xdf\x1b\xee'), None)
				self.assertIs(r.jtype(), hprof.jtype.int)
				self.assertEqual(r.jval(hprof.jtype.int), 0x00200061)
				self.assertEqual(r.jval(hprof.jtype.int), 0xd83ddf1b - 0x100000000)
				with self.assertRaises(hprof.error.UnexpectedEof):
					r.jval(hprof.jtype.int)

	def test_jlong(self):
		for t in (bytes, memoryview):
			with self.subTest(t):
				r = hprof._parsing.PrimitiveReader(t(b'\x0b\x80\x20\0\x61\xd8\x3d\xdf\x1b\xee'), None)
				self.assertIs(r.jtype(), hprof.jtype.long)
				self.assertEqual(r.jval(hprof.jtype.long), 0x80200061d83ddf1b - 0x10000000000000000)
				with self.assertRaises(hprof.error.UnexpectedEof):
					r.jval(hprof.jtype.long)

	def test_bad_jtype(self):
		for t in (bytes, memoryview):
			with self.subTest(t):
				r = hprof._parsing.PrimitiveReader(t(b'\x0c'), None)
				with self.assertRaises(hprof.error.FormatError):
					r.jtype()
				with self.assertRaisesRegex(ValueError, 'unhandled jval type'):
					r.jval('boolean')


class TestMutf8(unittest.TestCase):

	def decode(self, bytes):
		r = hprof._parsing.PrimitiveReader(bytes, 4)
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
