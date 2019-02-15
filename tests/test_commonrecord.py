#!/usr/bin/env python3
#coding=utf8

from unittest import TestCase
from hprof.commonrecord import CommonRecord

class TestCommonRecord(TestCase):
	def setUp(self):
		self.r = CommonRecord(None, 10)

	def test_commonrecord_no_len(self):
		with self.assertRaises(TypeError):
			len(self.r)

	# TODO: test immutability, unorderability (I _think_ that's a word... :)), and more...
