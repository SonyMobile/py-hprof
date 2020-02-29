import unittest
import hprof

class TestPerlerParsing(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		print()
		last = (None, None)
		def progress(action, pos, end):
			if pos is None:
				print('perler.hprof.bz2: %s...                \r' % action, end='')
			elif end is None:
				print('perler.hprof.bz2: %s %d                \r' % (action, pos), end='')
			else:
				nonlocal last
				percent = int(100 * pos / end)
				if last[0] != action or last[1] != percent:
					last = (action, percent)
					print('perler.hprof.bz2: %s %3d%%             \r' % last, end='')
		cls.hf = hprof.open('testdata/perler.hprof.bz2', progress)
		print('perler.hprof.bz2: file loaded!            ')

	@classmethod
	def tearDownClass(cls):
		cls.hf.close()

	def test_name_record_values(self):
		for nameid, expected in (
			(0x7ff7100edd10, '(Ljava/lang/String;I[Ljava/lang/String;[Ljava/lang/String;[I[I)V'),
			(0x7ff71012c2d0, 'initialising'),
			(0x7ff7100be3b0, 'InsertUndo'),
		):
			with self.subTest(nameid):
				self.assertEqual(self.hf.names[nameid], expected)

	def test_name_record_count(self):
		self.assertEqual(len(self.hf.names), 68327)

	def test_frame_record_values(self):
		#00000000 00000001 00007ff7 55fe3ac0 00007ff7 55fd53d0 00007ff7 55fe4290 00001002 fffffffd
		self.assertEqual(self.hf.stackframes[0x01].method, 'sleep')
		self.assertEqual(self.hf.stackframes[0x01].signature, '(J)V')
		self.assertEqual(self.hf.stackframes[0x01].sourcefile, 'Thread.java')
		self.assertIs(   self.hf.stackframes[0x01].class_name, self.hf.classloads[0x1002].class_name)
		self.assertEqual(self.hf.stackframes[0x01].line, -3)

		#00000000 0000000b 00007ff7 55fd6b90 00007ff7 4c3a1fd0 00000000 00000000 00000113 ffffffff
		self.assertEqual(self.hf.stackframes[0x0b].method, 'next')
		self.assertEqual(self.hf.stackframes[0x0b].signature, '()Lse/dolkow/imagefiltering/ThreadedCacher$Task;')
		self.assertIs(   self.hf.stackframes[0x0b].sourcefile, None)
		self.assertIs(   self.hf.stackframes[0x0b].class_name, self.hf.classloads[0x113].class_name)
		self.assertEqual(self.hf.stackframes[0x0b].line, -1)

		#00000000 0000001a 00007ff7 55fd1d70 00007ff7 55fd3330 00007ff7 55fd53e0 00001043 000001f6
		self.assertEqual(self.hf.stackframes[0x1a].method, 'wait')
		self.assertEqual(self.hf.stackframes[0x1a].signature, '()V')
		self.assertEqual(self.hf.stackframes[0x1a].sourcefile, 'Object.java')
		self.assertIs(   self.hf.stackframes[0x1a].class_name, self.hf.classloads[0x1043].class_name)
		self.assertEqual(self.hf.stackframes[0x1a].line, 0x1f6)

	def test_frame_record_count(self):
		self.assertEqual(len(self.hf.stackframes), 82)

	def test_trace_record_values(self):
		#00000001 00000000 00000000
		self.assertEqual(self.hf.stacktraces[0x01].thread, None)
		self.assertEqual(len(self.hf.stacktraces[0x01]), 0)

		#00000003 00000002 00000002 00000000 00000001 00000000 00000002
		self.assertEqual(self.hf.stacktraces[0x03].thread, 'dummy thread') # TODO: real Thread
		self.assertEqual(len(self.hf.stacktraces[0x03]), 2)
		self.assertIs(self.hf.stacktraces[0x03][0], self.hf.stackframes[0x01])
		self.assertIs(self.hf.stacktraces[0x03][1], self.hf.stackframes[0x02])

		#00000009 00000008 00000004 00000000 00000015
		#00000000 00000016 00000000 00000017 00000000 00000018
		self.assertEqual(self.hf.stacktraces[0x09].thread, 'dummy thread') # TODO: real Thread
		self.assertEqual(len(self.hf.stacktraces[0x09]), 4)
		self.assertIs(self.hf.stacktraces[0x09][0], self.hf.stackframes[0x15])
		self.assertIs(self.hf.stacktraces[0x09][1], self.hf.stackframes[0x16])
		self.assertIs(self.hf.stacktraces[0x09][2], self.hf.stackframes[0x17])
		self.assertIs(self.hf.stacktraces[0x09][3], self.hf.stackframes[0x18])

	def test_trace_record_count(self):
		self.assertEqual(len(self.hf.stacktraces), 23)

	def test_class_load_values(self):
		#00000001 00000000 cbc32588 00000001 00007ff6 d80d8a50
		self.assertEqual(self.hf.classloads[1].class_id, 0xcbc32588)
		self.assertEqual(self.hf.classloads[1].class_name, self.hf.names[0x7ff6d80d8a50])
		self.assertEqual(self.hf.classloads[1].stacktrace, self.hf.stacktraces[1])

		#00000404 00000000 cb172d80 00000001 00007ff7 10219230
		self.assertEqual(self.hf.classloads[0x404].class_id, 0xcb172d80)
		self.assertEqual(self.hf.classloads[0x404].class_name, self.hf.names[0x7ff710219230])
		self.assertEqual(self.hf.classloads[0x404].stacktrace, self.hf.stacktraces[1])

		#00001066 00000000 cb1e28e0 00000001 00007ff7 10148740
		self.assertEqual(self.hf.classloads[0x1066].class_id, 0xcb1e28e0)
		self.assertEqual(self.hf.classloads[0x1066].class_name, self.hf.names[0x7ff710148740])
		self.assertEqual(self.hf.classloads[0x1066].stacktrace, self.hf.stacktraces[1])

	def test_class_load_count(self):
		self.assertEqual(len(self.hf.classloads), 4198)

	def test_heap_count(self):
		self.assertEqual(len(self.hf.heaps), 1)

	def test_num_unhandled(self):
		self.assertEqual(sum(self.hf.unhandled.values()), 0)

	def test_class_lookup(self):
		heap, = self.hf.heaps
		self.assertEqual(heap.classtree.se.dolkow.imagefiltering.ShrinkFilter, 'se.dolkow.imagefiltering.ShrinkFilter')
		cls, = heap.classes['se.dolkow.imagefiltering.ShrinkFilter']
		abstract, = heap.classes['se.dolkow.imagefiltering.AbstractImageFilter']
		self.assertTrue(issubclass(cls, abstract))
		self.assertCountEqual(cls._hprof_ifields, ('maxw', 'maxh', 'smooth', 'resListener'))
		self.assertCountEqual(abstract._hprof_ifields, ('active', 'name', 'source', 'description'))

	def test_static_fields(self):
		heap, = self.hf.heaps
		filt, = heap.classes['se.dolkow.imagefiltering.AbstractReduceColorsFilter']
		self.assertEqual(filt.mult, 14)

	def test_instance_fields(self):
		heap, = self.hf.heaps
		abstract, = heap.classes['se.dolkow.imagefiltering.AbstractReduceColorsFilter']
		dithered, = heap.classes['se.dolkow.imagefiltering.DitherReduceColorsFilter']
		hashmap,  = heap.classes['java.util.HashMap']
		instance = heap[0xcb4bc498]
		self.assertIsInstance(instance, abstract)
		self.assertIsInstance(instance, dithered)
		self.assertEqual(instance.coeff, 0.800000011920929)
		self.assertIs(instance.colors, heap[0xcb4bc4d0])
		self.assertIsInstance(instance.colors, hashmap)

	def test_object_array(self):
		heap, = self.hf.heaps
		changecls, = heap.classes['se.dolkow.imagefiltering.DitherReduceColorsFilter.Change']
		changearr, = heap.classes['se.dolkow.imagefiltering.DitherReduceColorsFilter.Change[]']
		array = heap[0xcb1411e8]
		self.assertIsInstance(array, changearr)
		self.assertEqual(len(array), 4)
		self.assertIs(array[0], heap[0xcb141268])
		self.assertIs(array[1], heap[0xcb141248])
		self.assertIs(array[2], heap[0xcb141228])
		self.assertIs(array[3], heap[0xcb141208])
		self.assertIsInstance(array[0], changecls)
		self.assertIsInstance(array[1], changecls)
		self.assertIsInstance(array[2], changecls)
		self.assertIsInstance(array[3], changecls)
