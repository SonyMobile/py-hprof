from unittest import TestCase

import hprof

from .util import HprofBuilder, varying_idsize

@varying_idsize
class TestDumpAccess(TestCase):
	def setUp(self):
		hb = HprofBuilder(b'JAVA PROFILE 1.0.3\0', self.idsize, 123456)
		self.name_object   = hb.name(9100000, 'java.lang.Object')
		self.name_main     = hb.name(1300001, 'com.example.Main')
		self.name_buddy    = hb.name(4400002, 'com.example.Buddy')
		self.name_subbuddy = hb.name(1600003, 'com.example.SubBuddy')
		self.name_buddies  = hb.name(4500004, 'buddies')
		self.name_id       = hb.name(9900005, 'id')
		self.name_queue    = hb.name(7800006, 'queue')
		self.name_extra    = hb.name(6500007, 'extra')
		self.name_counter  = hb.name(1200008, 'counter')
		self.name_barray   = hb.name(1200009, 'com.example.Buddy[]')
		self.name_basic    = hb.name(1800010, 'basic')
		self.name_shortarr = hb.name(1700011, 'short[]')
		with hb.record(2, 0) as load:
			load.uint(1003) # serial number
			self.object_clsid = load.id(10101010)
			load.uint(1233) # stack trace serial
			load.id(self.name_object)
		with hb.record(2, 0) as load:
			load.uint(1002) # serial number
			self.subbuddy_clsid = load.id(181820)
			load.uint(1234) # stack trace serial
			load.id(self.name_subbuddy)
		with hb.record(2, 0) as load:
			load.uint(1000) # serial number
			self.main_clsid = load.id(123000000)
			load.uint(1234) # stack trace serial
			load.id(self.name_main)
		with hb.record(2, 0) as load:
			load.uint(1001) # serial number
			self.buddy_clsid = load.id(123)
			load.uint(1235) # stack trace serial
			load.id(self.name_buddy)
		with hb.record(2, 0) as load:
			load.uint(1005) # serial number
			self.shortarray_clsid = load.id(929292)
			load.uint(0) # stack trace serial
			load.id(self.name_shortarr)
		with hb.record(28, 0) as dump:
			with dump.subrecord(32) as clsShortArray:
				clsShortArray.id(self.shortarray_clsid)
				clsShortArray.uint(0)               # stack serial number
				clsShortArray.id(self.object_clsid) # super
				clsShortArray.id(0)                 # loader
				clsShortArray.id(0)                 # signer
				clsShortArray.id(0)                 # protection domain
				clsShortArray.id(0)                 # reserved1
				clsShortArray.id(0)                 # reserved2
				clsShortArray.uint(0)               # instance size
				# constant pool:
				clsShortArray.ushort(0) # count
				# static fields:
				clsShortArray.ushort(0) # count
				# instance fields:
				clsShortArray.ushort(0) # count
			with dump.subrecord(32) as clsSubBuddy:
				clsSubBuddy.id(self.subbuddy_clsid)
				clsSubBuddy.uint(1236)            # stack serial number
				clsSubBuddy.id(self.buddy_clsid)  # super
				clsSubBuddy.id(0)                 # loader
				clsSubBuddy.id(0)                 # signer
				clsSubBuddy.id(0)                 # protection domain
				clsSubBuddy.id(0)                 # reserved1
				clsSubBuddy.id(0)                 # reserved2
				clsSubBuddy.uint(20)              # instance size
				# constant pool:
				clsSubBuddy.ushort(0) # count
				# static fields:
				clsSubBuddy.ushort(1)             # count
				clsSubBuddy.id(self.name_counter) # field name
				clsSubBuddy.byte(9)               # field type (short)
				clsSubBuddy.short(-20000)         # field value
				# instance fields:
				clsSubBuddy.ushort(1)           # count
				clsSubBuddy.id(self.name_extra) # field name
				clsSubBuddy.byte(10)            # field type (int)
			with dump.subrecord(32) as clsBuddy:
				clsBuddy.id(self.buddy_clsid)
				clsBuddy.uint(1237)            # stack serial number
				clsBuddy.id(self.object_clsid) # super
				clsBuddy.id(0)                 # loader
				clsBuddy.id(0)                 # signer
				clsBuddy.id(0)                 # protection domain
				clsBuddy.id(0)                 # reserved1
				clsBuddy.id(0)                 # reserved2
				clsBuddy.uint(16)              # instance size
				# constant pool:
				clsBuddy.ushort(0) # count
				# static fields:
				clsBuddy.ushort(0) # count
				# instance fields:
				clsBuddy.ushort(1)        # count
				clsBuddy.id(self.name_id) # field name
				clsBuddy.byte(10)         # field type (int)
			with dump.subrecord(33) as main:
				self.main_id = main.id(784102)
				main.uint(0)
				main.id(self.main_clsid)
				main.uint(self.idsize)
				self.buddy_array_id = main.id(7000)
			with dump.subrecord(33) as buddy1:
				self.buddy1_id = buddy1.id(101)
				buddy1.uint(0)
				buddy1.id(self.buddy_clsid)
				buddy1.uint(4)
				buddy1.uint(10)
			with dump.subrecord(33) as buddy3:
				self.buddy3_id = buddy3.id(102)
				buddy3.uint(0)
				buddy3.id(self.buddy_clsid)
				buddy3.uint(4)
				buddy3.uint(300)
			with dump.subrecord(33) as buddy2:
				self.buddy2_id = buddy2.id(103)
				buddy2.uint(0)
				buddy2.id(self.subbuddy_clsid)
				buddy2.uint(8)
				buddy2.uint(6464)
				buddy2.uint(2000)
			with dump.subrecord(34) as buddyarray:
				buddyarray.id(self.buddy_array_id)
				buddyarray.uint(0)
				buddyarray.uint(3) # elem count
				self.barray_clsid = buddyarray.id(1084971)
				buddyarray.id(self.buddy1_id)
				buddyarray.id(self.buddy2_id)
				buddyarray.id(self.buddy3_id)
		with hb.record(2, 0) as load:
			load.uint(1004) # serial number
			load.id(self.barray_clsid)
			load.uint(0)
			load.id(self.name_barray)
		with hb.record(28, 0) as dump:
			with dump.subrecord(35) as queue:
				self.queue_id = queue.id(891624)
				queue.uint(0)
				queue.uint(5) # elem count
				queue.byte(9)  # elem type (short)
				queue.short(301)
				queue.short(3001)
				queue.short(0)
				queue.short(-30000)
				queue.short(30001)
			with dump.subrecord(32) as clsMain:
				clsMain.id(self.main_clsid)
				clsMain.uint(0)               # stack serial number
				clsMain.id(self.object_clsid) # super
				clsMain.id(0)                 # loader
				clsMain.id(0)                 # signer
				clsMain.id(0)                 # protection domain
				clsMain.id(0)                 # reserved1
				clsMain.id(0)                 # reserved2
				clsMain.uint(40)              # instance size
				# constant pool:
				clsMain.ushort(0) # count
				# static fields:
				clsMain.ushort(1)             # count
				clsMain.id(self.name_queue)   # field name
				clsMain.byte(2)               # field type (object)
				clsMain.id(self.queue_id)     # field value
				# instance fields:
				clsMain.ushort(1)             # count
				clsMain.id(self.name_buddies) # field name
				clsMain.byte(2)               # field type (object)
			with dump.subrecord(32) as clsBarray:
				clsBarray.id(self.barray_clsid)
				clsBarray.uint(0)               # stack serial number
				clsBarray.id(self.object_clsid) # super
				clsBarray.id(0)                 # loader
				clsBarray.id(0)                 # signer
				clsBarray.id(0)                 # prot. domain
				clsBarray.id(0)                 # reserved1
				clsBarray.id(0)                 # reserved1
				clsBarray.uint(0)               # instance size
				# constant pool:
				clsBarray.ushort(0) # count
				# static fields:
				clsBarray.ushort(0) # count
				# instance fields:
				clsBarray.ushort(0) # count
			with dump.subrecord(32) as clsObject:
				clsObject.id(self.object_clsid)
				clsObject.uint(0)  # stack serial number
				clsObject.id(0)    # 0 for no super class, I assume..?
				clsObject.id(0)    # loader
				clsObject.id(0)    # signer
				clsObject.id(0)    # prot. domain
				clsObject.id(0)    # reserved1
				clsObject.id(0)    # reserved1
				clsObject.uint(4)  # instance size
				# constant pool:
				clsObject.ushort(0) # count
				# static fields:
				clsObject.ushort(1) # count
				clsObject.id(self.name_basic)
				clsObject.byte(8)   # type (byte)
				clsObject.byte(33)  # value
				# instance fields:
				clsObject.ushort(0) # count

		self.addrs, self.data = hb.build()
		self.hf = hprof.open(bytes(self.data))
		self.dump, = self.hf.dumps()
		self.heap, = self.dump.heaps()
		(
			self.ShortArray, self.SubBuddy, self.Buddy, self.main,
			self.buddy1, self.buddy3, self.buddy2,
			self.buddyarray, self.queue,
			self.Main, self.BArray, self.Object,
		) = sorted(self.heap.objects(), key=lambda r: r.hprof_addr)

	def tearDown(self):
		self.hf.close()


	def test_access_main_instance_field_from_instance(self):
		self.assertEqual(self.main.buddies, self.buddyarray)

	def test_access_main_instance_field_from_class(self):
		with self.assertRaisesRegex(hprof.FieldNotFoundError, 'static field.*buddies.*Main.*Object'):
			self.Main.buddies

	def test_access_main_static_field_from_instance(self):
		self.assertEqual(self.main.queue, self.queue)

	def test_access_main_static_field_from_class(self):
		self.assertEqual(self.Main.queue, self.queue)


	def test_access_buddy_instance_field_from_instance(self):
		self.assertEqual(self.buddy1.id, 10)
		self.assertEqual(self.buddy2.id, 2000)
		self.assertEqual(self.buddy3.id, 300)

	def test_access_buddy_instance_field_from_class(self):
		with self.assertRaisesRegex(hprof.FieldNotFoundError, 'static field.*id.*Buddy.*Object'):
			self.Buddy.id


	def test_access_subbuddy_instance_field_from_instance(self):
		self.assertEqual(self.buddy2.extra, 6464)

	def test_access_subbuddy_instance_field_from_class(self):
		with self.assertRaisesRegex(hprof.FieldNotFoundError, 'static field.*extra.*SubBuddy.*Buddy.*Object'):
			self.SubBuddy.extra

	def test_access_subbuddy_instance_field_from_buddy(self):
		with self.assertRaisesRegex(hprof.FieldNotFoundError, 'static or instance.*extra.*Buddy.*Object'):
			self.buddy1.extra
		with self.assertRaisesRegex(hprof.FieldNotFoundError, 'static or instance.*extra.*Buddy.*Object'):
			self.buddy3.extra

	def test_access_subbuddy_instance_field_from_buddy_class(self):
		with self.assertRaisesRegex(hprof.FieldNotFoundError, 'static field.*extra.*Buddy.*Object'):
			self.Buddy.extra

	def test_access_subbuddy_static_field_from_instance(self):
		self.assertEqual(self.buddy2.counter, -20000)

	def test_access_subbuddy_static_field_from_class(self):
		self.assertEqual(self.SubBuddy.counter, -20000)

	def test_access_subbuddy_static_field_from_buddy(self):
		with self.assertRaisesRegex(hprof.FieldNotFoundError, 'static or instance.*counter.*Buddy.*Object'):
			self.assertEqual(self.buddy1.counter, -20000)
		with self.assertRaisesRegex(hprof.FieldNotFoundError, 'static or instance.*counter.*Buddy.*Object'):
			self.assertEqual(self.buddy3.counter, -20000)

	def test_access_subbuddy_static_field_from_buddy_class(self):
		with self.assertRaisesRegex(hprof.FieldNotFoundError, 'static field.*counter.*Buddy.*Object'):
			self.assertEqual(self.Buddy.counter, -20000)


	def test_access_buddyarray_length(self):
		self.assertEqual(self.buddyarray.length, 3)

	def test_access_buddyarray_values(self):
		self.assertEqual(self.buddyarray[0], self.buddy1)
		self.assertEqual(self.buddyarray[1], self.buddy2)
		self.assertEqual(self.buddyarray[2], self.buddy3)

	def test_access_buddyarray_values_through_main(self):
		self.assertEqual(self.main.buddies[0].id, 10)
		self.assertEqual(self.main.buddies[1].id, 2000)
		self.assertEqual(self.main.buddies[1].extra, 6464)
		self.assertEqual(self.main.buddies[2].id, 300)


	def test_access_object_static_field_through_classes(self):
		self.assertEqual(self.Object.basic, 33)
		self.assertEqual(self.Main.basic, 33)
		self.assertEqual(self.Buddy.basic, 33)
		self.assertEqual(self.SubBuddy.basic, 33)
		self.assertEqual(self.BArray.basic, 33)

	def test_access_object_static_field_through_instances(self):
		self.assertEqual(self.main.basic, 33)
		self.assertEqual(self.buddy1.basic, 33)
		self.assertEqual(self.buddy2.basic, 33)
		self.assertEqual(self.buddy3.basic, 33)
		self.assertEqual(self.buddyarray.basic, 33)
		self.assertEqual(self.queue.basic, 33)


	def test_access_buddyarray_missing(self):
		with self.assertRaisesRegex(hprof.FieldNotFoundError, 'static or instance.*missing.*Buddy\[\].*Object'):
			self.buddyarray.missing
		with self.assertRaisesRegex(hprof.FieldNotFoundError, 'static field.*missing.*Buddy\[\].*Object'):
			self.BArray.missing

	def test_access_primarray_missing(self):
		with self.assertRaisesRegex(hprof.FieldNotFoundError, 'static or instance.*missing.*short\[\].*Object'):
			self.queue.missing

	# TODO: test class name lookup!

	def test_hprof_get_class_info_object(self):
		info = self.hf.get_class_info(self.object_clsid)
		self.assertIs(type(info), hprof.record.ClassLoad)
		self.assertEqual(info.class_id, self.object_clsid)
		self.assertEqual(info.name, 'java.lang.Object')

	def test_hprof_get_class_info_object_array(self):
		info = self.hf.get_class_info(self.barray_clsid)
		self.assertIs(type(info), hprof.record.ClassLoad)
		self.assertEqual(info.class_id, self.barray_clsid)
		self.assertEqual(info.name, 'com.example.Buddy[]')

	def test_hprof_get_class_info_missing(self):
		with self.assertRaisesRegex(hprof.ClassNotFoundError, 'class id 0x123'):
			self.hf.get_class_info(0x123)

	def test_hprof_get_primitive_array_class_info(self):
		info = self.hf.get_primitive_array_class_info(hprof.JavaType.short)
		self.assertIs(type(info), hprof.record.ClassLoad)
		self.assertEqual(info.class_id, self.shortarray_clsid)
		self.assertEqual(info.name, 'short[]')

	def test_hprof_get_primitive_array_class_info_missing(self):
		with self.assertRaisesRegex(hprof.ClassNotFoundError, r'object\[\]'):
			self.hf.get_primitive_array_class_info(hprof.JavaType.object)

	def test_hprof_get_primitive_array_class_info_faketype(self):
		class FakeJavaType(object):
			name = 'something'
		with self.assertRaises(hprof.ClassNotFoundError):
			self.hf.get_primitive_array_class_info(FakeJavaType())
