import unittest
import hprof

from .util import varyingid, HeapRecordTest

@varyingid
class TestHeapObject(HeapRecordTest):
	# TODO real testing
	def test_minimal(self):
		self.doit(0x21, self.build()
				.id(0x0b1ec7) # object id
				.u4(0x57acc)  # stacktrace serial
				.id(0x2020)   # class id
				.u4(0x0)      # bytes remaining
		)
		# TODO: check the generated array

	def test_small(self):
		self.doit(0x21, self.build()
				.id(0x0b1ec7)   # object id
				.u4(0x57acc)    # stacktrace serial
				.id(0x2021)     # class id
				.u4(0x4)        # bytes remaining
				.u4(0x12345678) # first instance variable
		)
		# TODO: check the generated array
