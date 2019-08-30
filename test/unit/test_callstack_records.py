import unittest
import hprof

from .util import dehex

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
