
class TestShadowing(object):
	def setUp(self):
		self.heap, = self.hf.heaps
		self.cbase, = self.heap.classes['com.example.Base']
		self.ci,    = self.heap.classes['com.example.ShadowI']
		self.cs,    = self.heap.classes['com.example.ShadowS']
		self.cii,   = self.heap.classes['com.example.ShadowII']
		self.cis,   = self.heap.classes['com.example.ShadowIS']
		self.csi,   = self.heap.classes['com.example.ShadowSI']
		self.css,   = self.heap.classes['com.example.ShadowSS']

	def test_static_attr(self):
		for cls, expected in (
				(self.cbase, 10),
				(self.cs,    13),
				(self.cis,   11),
				(self.css,   12),
		):
			with self.subTest(cls=cls):
				with self.subTest(access='non-static'):
					obj, = self.heap.exact_instances(cls)
					self.assertEqual(obj.val, expected)
				with self.subTest(access='static'):
					self.assertEqual(cls.val, expected)

	def test_instance_attr(self):
		for cls, expected in (
				(self.ci,  4),
				(self.cii, 5),
				(self.csi, 6),
		):
			with self.subTest(cls=cls):
				with self.subTest(access='non-static'):
					obj, = self.heap.exact_instances(cls)
					self.assertEqual(obj.val, expected)
				with self.subTest(access='static'):
					pass # TODO:
					#with self.assertRaisesRegex(AttributeError, 'non-static'):
					#	cls.val
