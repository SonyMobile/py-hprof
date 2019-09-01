import unittest
import hprof

from .util import varyingid, HeapRecordTest

@varyingid
class TestGcRoots(HeapRecordTest):

	def test_unknown_root(self):
		self.doit(0xff, self.build().id(0xbadf00d))
		# TODO: check added root's attributes
		# TODO: do reference resolution, check results

	def test_global_jni_root(self):
		self.doit(0x01, self.build().id(0xbadf00d).id(0x5ef1d))
		# TODO: check added root's attributes
		# TODO: do reference resolution, check results

	def test_local_jni_root(self):
		self.doit(0x02, self.build().id(0xbadf00d).u4(0x752ead).i4(3))
		# TODO: check added root's attributes
		# TODO: do reference resolution, check results

	def test_java_stack_root(self):
		self.doit(0x03, self.build().id(0xbadf00d).u4(0x752ead).i4(-1))
		# TODO: check added root's attributes
		# TODO: do reference resolution, check results

	def test_native_stack_root(self):
		self.doit(0x04, self.build().id(0xbadf00d).u4(0x752ead))
		# TODO: check added root's attributes
		# TODO: do reference resolution, check results

	def test_sticky_class_root(self):
		self.doit(0x05, self.build().id(0xbadf00d))
		# TODO: check added root's attributes
		# TODO: do reference resolution, check results

	def test_thread_block_root(self):
		self.doit(0x06, self.build().id(0xbadf00d).u4(0x752ead))
		# TODO: check added root's attributes
		# TODO: do reference resolution, check results

	def test_monitor_root(self):
		self.doit(0x07, self.build().id(0xbadf00d))
		# TODO: check added root's attributes
		# TODO: do reference resolution, check results

	def test_thread_object_root(self):
		self.doit(0x08, self.build().id(0xbadf00d).u4(0x752ead).u4(0x57acc))
		# TODO: check added root's attributes
		# TODO: do reference resolution, check results
