from datetime import datetime, timedelta
from unittest import TestCase

import hprof

from .util import HprofBuilder, varying_idsize

@varying_idsize
class TestArtificialHprof(TestCase):
	def setUp(self):
		builder = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 0x168e143f263)
		with builder.record(255, 0) as r:
			r.uint(0x10203)
			r.bytes('Hello world!')
		with builder.record(255, 0x10000) as r:
			r.uint(0x03020101)
			r.bytes(b'\x50\xe5\xad\xa6\x51')
			r.bytes(b'ZYXWVUTSRQPONMLKJIHGFEDCBAabcdefghijklmnopqrstuvwxyz')
		with builder.record(255, 0x2000000) as r:
			r.uint(0x03040506)
			r.bytes('ABBA')
		with builder.record(255, 0) as r:
			pass
		self.addrs, self.data = builder.build()
		self.f = None

	def tearDown(self):
		self.close()

	def open(self):
		self.close()
		self.f = hprof.open(bytes(self.data))

	def close(self):
		if self.f is not None:
			self.f.close()
			self.f = None

	def test_correct_header(self):
		self.open()
		self.assertEqual(self.f.idsize, self.idsize)
		self.assertEqual(self.f.starttime, datetime.fromtimestamp(0x168E143F263/1000))

	def test_correct_modified_header(self):
		self.data[22] = 8
		self.data[25] = 0
		self.data[30] = 0x64
		self.open()
		self.assertEqual(self.f.idsize, 8)
		self.assertEqual(self.f.starttime, datetime.fromtimestamp(0x68E143F264/1000))

	def test_incorrect_header(self):
		self.data[7] = ord('Y')
		with self.assertRaisesRegex(hprof.FileFormatError, 'bad header'):
			self.open()

	def test_incorrect_version(self):
		self.data[13] = ord('9')
		with self.assertRaisesRegex(hprof.FileFormatError, 'bad version'):
			self.open()

	def test_list_0_records(self):
		self.data = self.data[:self.addrs[0]]
		self.open()
		recs = list(self.f.records())
		self.assertEqual(len(recs), 0)

	def test_list_1_record(self):
		self.data = self.data[:self.addrs[1]]
		self.open()
		recs = list(self.f.records())
		self.assertEqual(len(recs), 1)

	def test_list_2_records(self):
		self.data = self.data[:self.addrs[2]]
		self.open()
		recs = list(self.f.records())
		self.assertEqual(len(recs), 2)

	def test_list_3_records(self):
		self.data = self.data[:self.addrs[3]]
		self.open()
		recs = list(self.f.records())
		self.assertEqual(len(recs), 3)

	def test_iteration(self):
		self.data = self.data[:self.addrs[3]]
		self.open()
		recs = self.f.records()
		next(recs)
		next(recs)
		next(recs)
		with self.assertRaises(StopIteration):
			next(recs)

	def test_record_length(self):
		self.open()
		records = self.f.records()
		self.assertEqual(next(records)._hprof_len, 25)
		self.assertEqual(next(records)._hprof_len, 70)
		self.assertEqual(next(records)._hprof_len, 17)
		self.assertEqual(next(records)._hprof_len, 9)

	def test_record_time(self):
		self.open()
		base = 0x168e143f263 * 1000
		records = self.f.records()
		self.assertEqual(next(records).timestamp, datetime.fromtimestamp((base+0)/1000000))
		self.assertEqual(next(records).timestamp, datetime.fromtimestamp((base+0x10000)/1000000))
		self.assertEqual(next(records).timestamp, datetime.fromtimestamp((base+0x2000000)/1000000))
		self.assertEqual(next(records).timestamp, datetime.fromtimestamp((base+0)/1000000))

	def test_record_rawbody(self):
		self.open()
		recs = self.f.records()
		self.assertEqual(next(recs).rawbody, self.data[self.addrs[0]+9:self.addrs[1]])
		self.assertEqual(next(recs).rawbody, self.data[self.addrs[1]+9:self.addrs[2]])
		self.assertEqual(next(recs).rawbody, self.data[self.addrs[2]+9:self.addrs[3]])
		self.assertEqual(next(recs).rawbody, self.data[self.addrs[3]+9:])

	def test_record_str(self):
		self.open()
		for i, r in enumerate(self.f.records()):
			s = str(r)
			self.assertTrue(s.startswith('Unhandled('))
			self.assertTrue(s.endswith(')'))
			start = self.addrs[i]
			end = self.addrs[i+1] if i+1 < len(self.addrs) else len(self.data)
			block = self.data[start:end]
			self.assertIn(''.join('%02x' % b for b in block[ 9:13]), s)
			self.assertIn(''.join('%02x' % b for b in block[13:17]), s)
			self.assertIn(''.join('%02x' % b for b in block[17:21]), s)
			self.assertIn(''.join('%02x' % b for b in block[21:25]), s)

	def test_unhandled_record(self):
		self.open()
		records = self.f.records()
		next(records)
		r = next(records)
		self.assertIs(type(r), hprof.record.Unhandled)
		self.assertEqual(r.timestamp, datetime.fromtimestamp(0x168e143f263 / 1000 + 0x10000 / 1000000))
		self.assertEqual(r.relative_timestamp, timedelta(microseconds = 0x10000))
		self.assertEqual(r._hprof_len, 70)
		s = str(r)
		self.assertTrue(s.startswith('Unhandled('))
		self.assertTrue(s.endswith(')'))
		self.assertIn('03020101 50e5ada6', s)

@varying_idsize
class TestErrors(TestCase):
	def test_duplicate_id_error(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 0x12345)
		with hb.record(1, 3) as r:
			id1 = r.id(0x0102030405060708090a0b0c0d0e0f)
			r.bytes(b'string1')
		with hb.record(1, 5) as r:
			r.id(0x0102030405060708090a0b0c0d0e0f)
			r.bytes(b'string2')
		addrs, data = hb.build()
		hf = hprof.open(bytes(data))
		with self.assertRaisesRegex(hprof.FileFormatError, 'duplicate name id'):
			hf.name(id1)

	def test_duplicate_class_id_error(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 0x12345)
		hb.name(10, 'ClassA')
		hb.name(11, 'ClassB')
		with hb.record(2, 0) as load:
			load.uint(3)
			load.id(40)
			load.uint(0)
			load.id(10)
		with hb.record(2, 0) as load:
			load.uint(4)
			load.id(40)
			load.uint(0)
			load.id(11)
		addrs, data = hb.build()
		hf = hprof.open(bytes(data))
		with self.assertRaisesRegex(hprof.FileFormatError, 'duplicate class object id'):
			hf.get_class_info(500)

	def test_duplicate_class_name_okay(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 0x12345)
		hb.name(10, 'ClassA')
		with hb.record(2, 0) as load:
			load.uint(3)
			load.id(41)
			load.uint(0)
			load.id(10)
		with hb.record(2, 0) as load:
			load.uint(4)
			load.id(40)
			load.uint(0)
			load.id(10)
		with hb.record(28, 0) as dump:
			pass
		addrs, data = hb.build()
		hf = hprof.open(bytes(data))
		one = hf.get_class_info(40)
		two = hf.get_class_info(41)
		self.assertNotEqual(one, two)
		self.assertEqual(one.class_id, 40)
		self.assertEqual(two.class_id, 41)
		self.assertEqual(one.class_name, 'ClassA')
		self.assertEqual(two.class_name, 'ClassA')
		self.assertCountEqual(hf.get_class_infos('ClassA'), (one, two))
		dump, = hf.dumps()
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'Multiple'):
			dump.get_class('ClassA')
