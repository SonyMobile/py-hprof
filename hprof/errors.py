#!/usr/bin/env python3
#coding=utf8


class Error(Exception):
	pass

class FileFormatError(Error):
	pass

class EofError(Error):
	pass

class RefError(Error):
	pass
