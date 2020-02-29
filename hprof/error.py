class HprofError(Exception): pass
class FormatError(HprofError): pass
class UnexpectedEof(HprofError): pass
class UnhandledError(HprofError): pass
class MissingObject(HprofError): pass
