# Copyright (C) 2019 Snild Dolkow
# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

# pylint: disable=multiple-statements

'''
Various errors that hprof may raise.
'''

class HprofError(Exception):
	''' Base class of all errors from the hprof library '''
class FormatError(HprofError):
	''' Raised when we could not make sense of the file data. '''
class UnexpectedEof(HprofError):
	''' Raised when the file data ended at an unexpected point. '''
class UnhandledError(HprofError):
	''' Raised for any unexpected error that hprof encounters. '''
class MissingObject(HprofError):
	''' Raised when a referenced object could not be found. '''

