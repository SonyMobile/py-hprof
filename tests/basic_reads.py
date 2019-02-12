#!/usr/bin/env python3
#coding=utf8

from unittest import main, TestCase

from env import hprof, find

class TestCorners(TestCase):
	def test_modify_data(self):
		with hprof.BinaryFile(find('basic_reads.hprof')) as bf:
			with self.assertRaises(TypeError):
				bf._data[0] = 0x20

	def test_exit_cleanup(self):
		with hprof.BinaryFile(find('basic_reads.hprof')) as bf:
			pass
		self.assertIsNone(bf._data)
		self.assertIsNone(bf._f)

class TestByteReads(TestCase):
	def setUp(self):
		self.f = hprof.BinaryFile(find('basic_reads.hprof'))

	def tearDown(self):
		self.f.close()

	def test_read_byte(self):
		self.assertEqual(self.f.read_byte( 0), 0x41)
		self.assertEqual(self.f.read_byte( 1), 0x42)
		self.assertEqual(self.f.read_byte( 2), 0x43)
		self.assertEqual(self.f.read_byte( 3), 0x44)
		self.assertEqual(self.f.read_byte( 4), 0)
		self.assertEqual(self.f.read_byte( 5), 0)
		self.assertEqual(self.f.read_byte( 6), 0)
		self.assertEqual(self.f.read_byte( 7), 0)
		self.assertEqual(self.f.read_byte( 8), 0xc3)
		self.assertEqual(self.f.read_byte( 9), 0xb6)
		self.assertEqual(self.f.read_byte(10), 0x46)
		self.assertEqual(self.f.read_byte(11), 0x00)
		self.assertEqual(self.f.read_byte(12), 0xaa)
		self.assertEqual(self.f.read_byte(13), 0x46)
		self.assertEqual(self.f.read_byte(14), 0x47)
		self.assertEqual(self.f.read_byte(15), 0x48)
		self.assertEqual(self.f.read_byte(16), 0x49)

	def test_read_byte_outside(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_byte(17)

	def test_read_byte_negative(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_byte(-1)

class TestUintReads(TestCase):
	def setUp(self):
		self.f = hprof.BinaryFile(find('basic_reads.hprof'))

	def tearDown(self):
		self.f.close()

	def test_read_uint(self):
		self.assertEqual(self.f.read_uint( 0), 0x41424344)
		self.assertEqual(self.f.read_uint( 1), 0x42434400)
		self.assertEqual(self.f.read_uint( 2), 0x43440000)
		self.assertEqual(self.f.read_uint( 3), 0x44000000)
		self.assertEqual(self.f.read_uint( 4), 0)
		self.assertEqual(self.f.read_uint( 5), 0x000000c3)
		self.assertEqual(self.f.read_uint( 6), 0x0000c3b6)
		self.assertEqual(self.f.read_uint( 7), 0x00c3b646)
		self.assertEqual(self.f.read_uint( 8), 0xc3b64600)
		self.assertEqual(self.f.read_uint( 9), 0xb64600aa)
		self.assertEqual(self.f.read_uint(10), 0x4600aa46)
		self.assertEqual(self.f.read_uint(11), 0x00aa4647)
		self.assertEqual(self.f.read_uint(12), 0xaa464748)
		self.assertEqual(self.f.read_uint(13), 0x46474849)

	def test_read_uint_spill(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_uint(15)

	def test_read_uint_outside(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_uint(2000)

	def test_read_uint_negative(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_uint(-2)

class TestIntReads(TestCase):
	def setUp(self):
		self.f = hprof.BinaryFile(find('basic_reads.hprof'))

	def tearDown(self):
		self.f.close()

	def test_read_uint(self):
		self.assertEqual(self.f.read_int( 0), 0x41424344)
		self.assertEqual(self.f.read_int( 1), 0x42434400)
		self.assertEqual(self.f.read_int( 2), 0x43440000)
		self.assertEqual(self.f.read_int( 3), 0x44000000)
		self.assertEqual(self.f.read_int( 4), 0)
		self.assertEqual(self.f.read_int( 5), 0x000000c3)
		self.assertEqual(self.f.read_int( 6), 0x0000c3b6)
		self.assertEqual(self.f.read_int( 7), 0x00c3b646)
		self.assertEqual(self.f.read_int( 8), -0x3c49ba00)
		self.assertEqual(self.f.read_int( 9), -((~0xb64600aa+1) % (2**32)))
		self.assertEqual(self.f.read_int(10), 0x4600aa46)
		self.assertEqual(self.f.read_int(11), 0x00aa4647)
		self.assertEqual(self.f.read_int(12), -((~0xaa464748+1) % (2**32)))
		self.assertEqual(self.f.read_int(13), 0x46474849)

	def test_read_int_spill(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_uint(15)

	def test_read_int_outside(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_uint(2000)

	def test_read_int_negative(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_uint(-2)


class TestAsciiReads(TestCase):
	def setUp(self):
		self.f = hprof.BinaryFile(find('basic_reads.hprof'))

	def tearDown(self):
		self.f.close()

	def test_read_ascii_fixed1(self):
		self.assertEqual(self.f.read_ascii(0, 1), 'A')
		self.assertEqual(self.f.read_ascii(1, 1), 'B')
		self.assertEqual(self.f.read_ascii(2, 1), 'C')
		self.assertEqual(self.f.read_ascii(3, 1), 'D')
		self.assertEqual(self.f.read_ascii(4, 1), '\0')

	def test_read_ascii_fixed2(self):
		self.assertEqual(self.f.read_ascii(0, 2), 'AB')
		self.assertEqual(self.f.read_ascii(1, 2), 'BC')
		self.assertEqual(self.f.read_ascii(2, 2), 'CD')
		self.assertEqual(self.f.read_ascii(3, 2), 'D\0')

	def test_read_ascii_fixed3(self):
		self.assertEqual(self.f.read_ascii(0, 3), 'ABC')
		self.assertEqual(self.f.read_ascii(1, 3), 'BCD')
		self.assertEqual(self.f.read_ascii(2, 3), 'CD\0')

	def test_read_ascii_fixed4(self):
		self.assertEqual(self.f.read_ascii(0, 4), 'ABCD')
		self.assertEqual(self.f.read_ascii(1, 4), 'BCD\0')
		self.assertEqual(self.f.read_ascii(2, 4), 'CD\0\0')

	def test_read_ascii_fixed5(self):
		self.assertEqual(self.f.read_ascii(0, 5), 'ABCD\0')
		self.assertEqual(self.f.read_ascii(1, 5), 'BCD\0\0')

	def test_read_terminated_ascii(self):
		self.assertEqual(self.f.read_ascii(0), 'ABCD')
		self.assertEqual(self.f.read_ascii(1), 'BCD')
		self.assertEqual(self.f.read_ascii(2), 'CD')
		self.assertEqual(self.f.read_ascii(3), 'D')
		self.assertEqual(self.f.read_ascii(4), '')
		self.assertEqual(self.f.read_ascii(5), '')

	def test_read_invalid_ascii(self):
		with self.assertRaises(UnicodeError):
			self.f.read_ascii(8)

	def test_read_ascii_fixed_spill(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_ascii(15,10)

	def test_read_ascii_fixed_outside(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_ascii(20, 2)

	def test_read_ascii_fixed_negative(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_ascii(-1, 1)

	def test_read_ascii_fixed_negative_len(self):
		with self.assertRaises(ValueError):
			self.f.read_ascii(3, -2)

	def test_read_terminated_ascii_spill(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_ascii(15)

	def test_read_terminated_ascii_outside(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_ascii(20)

	def test_read_terminated_ascii_negative(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_ascii(-4)

class TestUtf8Reads(TestCase):
	def setUp(self):
		self.f = hprof.BinaryFile(find('basic_reads.hprof'))

	def tearDown(self):
		self.f.close()

	def test_read_utf8_fixed1(self):
		self.assertEqual(self.f.read_utf8(0, 1), 'A')
		self.assertEqual(self.f.read_utf8(1, 1), 'B')
		self.assertEqual(self.f.read_utf8(2, 1), 'C')
		self.assertEqual(self.f.read_utf8(3, 1), 'D')
		self.assertEqual(self.f.read_utf8(4, 1), '\0')

	def test_read_utf8_fixed2(self):
		self.assertEqual(self.f.read_utf8(0, 2), 'AB')
		self.assertEqual(self.f.read_utf8(1, 2), 'BC')
		self.assertEqual(self.f.read_utf8(2, 2), 'CD')
		self.assertEqual(self.f.read_utf8(3, 2), 'D\0')

	def test_read_utf8_fixed3(self):
		self.assertEqual(self.f.read_utf8(0, 3), 'ABC')
		self.assertEqual(self.f.read_utf8(1, 3), 'BCD')
		self.assertEqual(self.f.read_utf8(2, 3), 'CD\0')

	def test_read_utf8_fixed4(self):
		self.assertEqual(self.f.read_utf8(0, 4), 'ABCD')
		self.assertEqual(self.f.read_utf8(1, 4), 'BCD\0')
		self.assertEqual(self.f.read_utf8(2, 4), 'CD\0\0')

	def test_read_utf8_fixed5(self):
		self.assertEqual(self.f.read_utf8(0, 5), 'ABCD\0')
		self.assertEqual(self.f.read_utf8(1, 5), 'BCD\0\0')

	def test_read_swedish_utf8(self):
		self.assertEqual(self.f.read_utf8(8, 3), 'öF')

	def test_read_incomplete_utf8(self):
		with self.assertRaises(UnicodeError):
			self.f.read_utf8(9, 2)

	def test_read_truncated_utf8(self):
		with self.assertRaises(UnicodeError):
			self.f.read_utf8(8, 1)

	def test_read_utf8_fixed_spill(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_utf8(15,10)

	def test_read_utf8_fixed_outside(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_utf8(20, 2)

	def test_read_utf8_fixed_negative(self):
		with self.assertRaises(hprof.EofError):
			self.f.read_utf8(-1, 1)

	def test_read_utf8_fixed_negative_len(self):
		with self.assertRaises(ValueError):
			self.f.read_utf8(3, -2)

class TestStream(TestCase):
	def setUp(self):
		self.f = hprof.BinaryFile(find('basic_reads.hprof'))

	def tearDown(self):
		self.f.close()

	def test_uint_stream(self):
		s = self.f.stream()
		self.assertEqual(s.read_uint(), 0x41424344)
		self.assertEqual(s.read_uint(), 0)
		self.assertEqual(s.read_uint(), 0xc3b64600)
		self.assertEqual(s.read_uint(), 0xaa464748)
		with self.assertRaises(hprof.EofError):
			s.read_uint()

	def test_int_stream(self):
		s = self.f.stream()
		self.assertEqual(s.read_int(), 0x41424344)
		self.assertEqual(s.read_int(), 0)
		self.assertEqual(s.read_int(), -0x3c49ba00)
		self.assertEqual(s.read_int(), -0x55b9b8b8)
		with self.assertRaises(hprof.EofError):
			s.read_int()

	def test_mixed_stream(self):
		s = self.f.stream()
		self.assertEqual(s.read_ascii(), 'ABCD')
		self.assertEqual(s.read_uint(), 0xc3)
		self.assertEqual(s.read_int(), -0x49b9ff56)
		self.assertEqual(s.read_ascii(2), 'FG')
		with self.assertRaises(hprof.EofError):
			s.read_ascii(4)
		self.assertEqual(s.read_ascii(2), 'HI')

	def test_skip(self):
		s = self.f.stream()
		self.assertEqual(s.read_ascii(), 'ABCD')
		s.skip(3)
		self.assertEqual(s.read_uint(), 0xc3b64600)

	def test_skip_first(self):
		s = self.f.stream()
		s.skip(1)
		self.assertEqual(s.read_ascii(), 'BCD')

	def test_skip_negative(self):
		s = self.f.stream()
		s.read_ascii()
		s.skip(-3)
		self.assertEqual(s.read_ascii(), 'CD')
		s.skip(-4)
		self.assertEqual(s.read_ascii(), 'BCD')

	def test_skip_outside(self):
		s = self.f.stream()
		s.read_ascii()
		s.skip(-4)
		with self.assertRaises(hprof.EofError):
			s.skip(-4)
		self.assertEqual(s.read_ascii(), 'BCD')
		s.skip(8)
		with self.assertRaises(hprof.EofError):
			s.skip(7)
		with self.assertRaises(hprof.EofError):
			s.skip(6)
		with self.assertRaises(hprof.EofError):
			s.skip(5)
		s.skip(4)
		with self.assertRaises(hprof.EofError):
			s.skip(1)
		s.skip(-2)
		self.assertEqual(s.read_ascii(2), 'HI')

	def test_jump_forward(self):
		s = self.f.stream()
		s.read_ascii()
		s.jump_to(10)
		self.assertEqual(s.read_ascii(1), 'F')

	def test_jump_forward_from_start(self):
		s = self.f.stream()
		s.jump_to(10)
		self.assertEqual(s.read_uint(), 0x4600aa46)

	def test_jump_backward(self):
		s = self.f.stream()
		s.read_ascii()
		s.jump_to(2)
		self.assertEqual(s.read_ascii(), 'CD')
		s.jump_to(0)
		self.assertEqual(s.read_ascii(), 'ABCD')

	def test_jump_outside(self):
		s = self.f.stream()
		s.jump_to(3)
		with self.assertRaises(hprof.EofError):
			s.jump_to(-2)
		with self.assertRaises(hprof.EofError):
			s.jump_to(18)
		self.assertEqual(s.read_ascii(), 'D')
		s.jump_to(17)
		with self.assertRaises(hprof.EofError):
			s.read_ascii(1)

	def test_pos_after_invalid_ascii(self):
		s = self.f.stream()
		s.jump_to(8)
		with self.assertRaises(UnicodeError):
			s.read_ascii()
		self.assertEqual(s.read_uint(), 0xc3b64600) # the failed ascii read didn't consume anything.

	def test_pos_after_spill(self):
		s = self.f.stream()
		s.jump_to(15)
		with self.assertRaises(hprof.EofError):
			s.read_uint()
		self.assertEqual(s.read_ascii(2), 'HI')

	def test_concurrent_streams(self):
		s = self.f.stream()
		t = self.f.stream()
		self.assertEqual(s.read_ascii(), 'ABCD')
		self.assertEqual(t.read_ascii(), 'ABCD')
		self.assertEqual(s.read_uint(), 0xc3)
		self.assertEqual(t.read_ascii(), '')
		self.assertEqual(s.read_uint(), 0xb64600aa)
		self.assertEqual(s.read_uint(), 0x46474849)
		self.assertEqual(t.read_uint(), 0xc3b6)
		s.jump_to(14)
		self.assertEqual(s.read_ascii(3), 'GHI')
		self.assertEqual(t.read_uint(), 0x4600aa46)

	def test_concurrent_stream_and_random_read(self):
		s = self.f.stream()
		self.assertEqual(s.read_ascii(), 'ABCD')
		self.assertEqual(self.f.read_ascii(13, 3), 'FGH')
		self.assertEqual(s.read_uint(), 0xc3)


if __name__ == '__main__':
    main()

