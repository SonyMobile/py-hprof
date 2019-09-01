import unittest
import hprof

from .util import varyingid, HeapRecordTest

@varyingid
class TestPrimitiveArray(HeapRecordTest):
	# TODO real testing
	def test_minimal(self):
		self.doit(0x23, self.build()
				.id(0x0b1ec7) # array id
				.u4(0x57acc)  # stacktrace serial
				.u4(0x0)      # length
				.u1(4)        # element type (boolean)
		)
		# TODO: check the generated array

	def test_small(self):
		self.doit(0x23, self.build()
				.id(0x0b1ec7) # array id
				.u4(0x57acc)  # stacktrace serial
				.u4(0x1)      # length
				.u1(9)        # element type (short)
				.u2(0xbea7)   # element 0
		)
		# TODO: check the generated array
