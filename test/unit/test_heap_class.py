import unittest
import hprof

from .util import varyingid, HeapRecordTest

@varyingid
class TestHeapClass(HeapRecordTest):
	# TODO real testing
	def test_minimal(self):
		self.doit(0x20, self.build()
				.id(0x0b1ec7)  # class object id
				.u4(0x123)     # stacktrace serial
				.id(0x500be2)  # superclass id
				.id(0x10ade2)  # loader id
				.id(0x5151515) # signer id
				.id(0x5ec002e) # protection domain id
				.id(0x999999)  # reserved 1
				.id(0xaaaaaa)  # reserved 2
				.u4(0x40)      # instance size
				.u2(0x0)       # constant pool size
				.u2(0x0)       # static field count
				.u2(0x0)       # instance field count
		)
		# TODO: check the generated class object

	def test_small(self):
		self.doit(0x20, self.build()
				.id(0x0b1ec7)  # class object id
				.u4(0x123)     # stacktrace serial
				.id(0x500be2)  # superclass id
				.id(0x10ade2)  # loader id
				.id(0x5151515) # signer id
				.id(0x5ec002e) # protection domain id
				.id(0x999999)  # reserved 1
				.id(0xaaaaaa)  # reserved 2
				.u4(0x40)      # instance size
				.u2(0x1)       # constant pool size
					.u2(0x0)   # constant pool index
					.u1(4)     # type (boolean)
					.u1(1)     # value (true)
				.u2(0x1)       # static field count
					.id(0xf00) # field name
					.u1(11)    # field type (long)
					.u8(70000) # field value
				.u2(0x1)       # instance field count
					.id(0xbaa) # field name
					.u1(10)    # field type (int)
		)
		# TODO: check the generated class object
