import unittest
import hprof

from .util import varyingid, HeapRecordTest

@varyingid
class TestHeapInfo(HeapRecordTest):
	def test_heap_info_parsing(self):
		self.doit(0xfe, self.build().u4(0xabcd).id(0xf00f00f00f00))

	# TODO: test access to this info
