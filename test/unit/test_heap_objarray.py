import unittest
import hprof

from .util import varyingid, HeapRecordTest

@varyingid
class TestObjectArray(HeapRecordTest):
	# TODO real testing
	def test_minimal(self):
		self.doit(0x22, self.build()
				.id(0x0b1ec7) # array id
				.u4(0x57acc)  # stack trace serial
				.u4(0x0)      # length
				.id(0x1010)   # class id
		)
		# TODO: check the generated object

	def test_small(self):
		self.doit(0x22, self.build()
				.id(0x0b1ec7) # array id
				.u4(0x57acc)  # stack trace serial
				.u4(0x1)      # length
				.id(0x1010)   # class id
				.id(0xf00baa) # element 0
		)
		# TODO: check the generated object
