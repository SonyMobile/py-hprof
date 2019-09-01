import unittest
import hprof

from .util import varyingid

@varyingid
class TestParseStackTraceRecords(unittest.TestCase):

	def setUp(self):
		self.hf.names[self.id(0x82104030)] = 'hello'
		self.hf.names[self.id(0x55555555)] = 'five'
		self.hf.names[self.id(0x08070605)] = 'dec'
		self.hf.names[self.id(0x10)] = 'sixteen'
		self.hf.names[self.id(0x11)] = 'moreThanSixteen'
		self.hf.names[self.id(0xdead)] = '()V'
		self.hf.names[self.id(0xf00d)] = '(Ljava/lang/String;)I'
		assert len(self.hf.names) == 8, repr(self.hf.names) # no dupes.
		self.dummythread = 'I am definitely a thread'
		self.hf.threads[0x10000000] = self.dummythread
		self.hf.classloads[0x12345678] = hprof._parsing.ClassLoad()
		self.hf.classloads[0x12345678].class_name = 'java.lang.String'
		self.hf.classloads[0x22345678] = hprof._parsing.ClassLoad()
		self.hf.classloads[0x22345678].class_name = 'com.example.pkg.SomeClass'

	def addframe(self, indata):
		reader = hprof._parsing.PrimitiveReader(memoryview(indata), self.idsize)
		hprof._parsing.record_parsers[0x04](self.hf, reader, None)

	def addstack(self, indata):
		reader = hprof._parsing.PrimitiveReader(memoryview(indata), self.idsize)
		hprof._parsing.record_parsers[0x05](self.hf, reader, None)

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
		self.assertEqual(frame.class_name, 'java.lang.String')
		self.assertEqual(frame.line, 0x51)

	def test_negative_line(self):
		self.addframe(self.build()
				.id(0x02030405).id(0x55555555).id(0xdead)
				.id(0x82104030).u4(0x12345678).i4(-2))
		fid = self.id(0x02030405)
		self.assertIn(fid, self.hf.stackframes)
		frame = self.hf.stackframes[fid]
		self.assertIsInstance(frame, hprof.callstack.Frame)
		self.assertEqual(frame.class_name, 'java.lang.String')
		self.assertEqual(frame.method, 'five')
		self.assertEqual(frame.signature, '()V')
		self.assertEqual(frame.sourcefile, 'hello')
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
		self.addstack(self.build()
				.u4(0x00000001).u4(0x0)
				.u4(2).id(0x03030404).id(0x03030407))
		self.addstack(self.build()
				.u4(0x03030404).u4(0x10000000)
				.u4(4).id(0x03030407).id(0x03030404).id(0x03030404).id(0x03030404))

		fid1 = self.id(0x03030404)
		fid2 = self.id(0x03030407)
		self.assertIn(fid1, self.hf.stackframes)
		self.assertIn(fid2, self.hf.stackframes)

		frame = self.hf.stackframes[fid1]
		self.assertIsInstance(frame, hprof.callstack.Frame)
		self.assertEqual(frame.class_name, 'java.lang.String')
		self.assertEqual(frame.method, 'hello')
		self.assertEqual(frame.signature, '(Ljava/lang/String;)I')
		self.assertEqual(frame.sourcefile, 'moreThanSixteen')
		self.assertEqual(frame.line, -1)

		frame = self.hf.stackframes[fid2]
		self.assertIsInstance(frame, hprof.callstack.Frame)
		self.assertEqual(frame.class_name, 'com.example.pkg.SomeClass')
		self.assertEqual(frame.method, 'sixteen')
		self.assertEqual(frame.signature, 'five')
		self.assertEqual(frame.sourcefile, 'dec')
		self.assertEqual(frame.line, 0x171)

		s1 = 0x00000001 # u4; not id.
		s2 = 0x03030404 # same as a stack id; no problem!
		self.assertIn(s1, self.hf.stacktraces)
		self.assertIn(s2, self.hf.stacktraces)

		stack = self.hf.stacktraces[s1]
		self.assertIsInstance(stack, hprof.callstack.Trace)
		self.assertIs(stack.thread, None)
		self.assertEqual(len(stack), 2)
		self.assertIs(stack[0], self.hf.stackframes[fid1])
		self.assertIs(stack[1], self.hf.stackframes[fid2])

		stack = self.hf.stacktraces[s2]
		self.assertIsInstance(stack, hprof.callstack.Trace)
		self.assertIs(stack.thread, self.dummythread)
		self.assertEqual(len(stack), 4)
		self.assertIs(stack[0], self.hf.stackframes[fid2])
		self.assertIs(stack[1], self.hf.stackframes[fid1])
		self.assertIs(stack[2], self.hf.stackframes[fid1])
		self.assertIs(stack[3], self.hf.stackframes[fid1])

	def test_stack_dummy_thread(self):
		self.addstack(self.build().u4(1).u4(0x2020).u4(0))
		trace = self.hf.stacktraces[1]
		# TODO: when Thread class exists, check that we have one (with appropriate values)
		self.assertEqual(trace.thread, 'dummy thread')

	def test_empty_stack(self):
		self.addstack(self.build().u4(1).u4(0x2020).u4(0))
		self.assertIn(1, self.hf.stacktraces)
		self.assertEqual(len(self.hf.stacktraces[1]), 0)

	def test_duplicate_stack(self):
		self.addstack(self.build().u4(1).u4(0x2020).u4(0))
		with self.assertRaisesRegex(hprof.error.FormatError, 'duplicate'):
			self.addstack(self.build().u4(1).u4(0x2120).u4(0))
