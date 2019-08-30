import unittest
import hprof

from .util import varyingid

@varyingid
class TestParseStackTraceRecords(unittest.TestCase):

	def setUp(self):
		self.hf = hprof._parsing.HprofFile()
		self.hf.idsize = self.idsize
		self.hf.names[self.id(0x82104030)] = 'hello'
		self.hf.names[self.id(0x55555555)] = 'five'
		self.hf.names[self.id(0x08070605)] = 'dec'
		self.hf.names[self.id(0x10)] = 'sixteen'
		self.hf.names[self.id(0x11)] = 'moreThanSixteen'
		self.hf.names[self.id(0xdead)] = '()V'
		self.hf.names[self.id(0xf00d)] = '(Ljava/lang/String;)I'
		assert len(self.hf.names) == 8, repr(self.hf.names) # no dupes.

	def addframe(self, indata):
		reader = hprof._parsing.PrimitiveReader(memoryview(indata))
		hprof._parsing.record_parsers[0x04](self.hf, reader)

	def addstack(self, indata):
		reader = hprof._parsing.PrimitiveReader(memoryview(indata))
		hprof._parsing.parse_stack_frame_record(self.hf, reader)

	def test_frame_only(self):
		self.addframe(self.build()
				.id(0x02030405).id(0x55555555).id(0xdead)
				.id(0x82104030).u4(0x12345678).i4(0x51))
		fid = self.id(0x02030405)
		self.assertIn(fid, self.hf.stackframes)
		frame = self.hf.stackframes[fid]
		self.assertIsInstance(frame, hprof.callstack.Frame)
		self.assertEqual(frame.method, 'five')
		self.assertEqual(frame.signature, '()V')
		self.assertEqual(frame.sourcefile, 'hello')
		# TODO: check class (need to handle class load records first)
		self.assertEqual(frame.line, 0x51)

	def test_negative_line(self):
		self.addframe(self.build()
				.id(0x02030405).id(0x55555555).id(0xdead)
				.id(0x82104030).u4(0x12345678).i4(-2))
		fid = self.id(0x02030405)
		self.assertIn(fid, self.hf.stackframes)
		frame = self.hf.stackframes[fid]
		self.assertIsInstance(frame, hprof.callstack.Frame)
		self.assertEqual(frame.method, 'five')
		self.assertEqual(frame.signature, '()V')
		self.assertEqual(frame.sourcefile, 'hello')
		# TODO: check class (need to handle class load records first)
		self.assertEqual(frame.line, -2)

	def test_duplicate_id(self):
		self.addframe(self.build()
				.id(0x02030405).id(0x55555555).id(0xdead)
				.id(0x82104030).u4(0x12345678).i4(0x51))
		with self.assertRaisesRegex(hprof.error.FormatError, 'duplicate'):
			self.addframe(self.build()
					.id(0x02030405).id(0x55555555).id(0xdead)
					.id(0x82104030).u4(0x12345678).i4(-2))

	def test_multiple_frames(self):
		self.addframe(self.build()
				.id(0x03030404).id(0x82104030).id(0xf00d)
				.id(0x00000011).u4(0x12345678).i4(-1))
		self.addframe(self.build()
				.id(0x03030407).id(0x00000010).id(0x55555555)
				.id(0x08070605).u4(0x22345678).i4(0x171))
		fid1 = self.id(0x03030404)
		fid2 = self.id(0x03030407)
		self.assertIn(fid1, self.hf.stackframes)
		self.assertIn(fid2, self.hf.stackframes)

		frame = self.hf.stackframes[fid1]
		self.assertIsInstance(frame, hprof.callstack.Frame)
		self.assertEqual(frame.method, 'hello')
		self.assertEqual(frame.signature, '(Ljava/lang/String;)I')
		self.assertEqual(frame.sourcefile, 'moreThanSixteen')
		self.assertEqual(frame.line, -1)

		frame = self.hf.stackframes[fid2]
		self.assertIsInstance(frame, hprof.callstack.Frame)
		self.assertEqual(frame.method, 'sixteen')
		self.assertEqual(frame.signature, 'five')
		self.assertEqual(frame.sourcefile, 'dec')
		self.assertEqual(frame.line, 0x171)
