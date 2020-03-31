# Copyright (C) 2019 Snild Dolkow
# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

# pylint: disable=multiple-statements

class HprofError(Exception): pass
class FormatError(HprofError): pass
class UnexpectedEof(HprofError): pass
class UnhandledError(HprofError): pass
class MissingObject(HprofError): pass
