from . import record
from .error import *

class HprofFile(object):
	def __init__(self):
		self.records = []
		self.names = {}

def open(path):
	if path.endswith('.bz2'):
		import bz2
		with bz2.open(path, 'rb') as f:
			return parse(f)
	elif path.endswith('.gz'):
		import gzip
		with gzip.open(path, 'rb') as f:
			return parse(f)
	elif path.endswith('.xz'):
		import lzma
		with lzma.open(path, 'rb') as f:
			return parse(f)
	else:
		import builtins
		with builtins.open(path, 'rb') as f:
			return parse(f)

def parse(data):
	failures = []

	# is it a bytes-like?
	try:
		with memoryview(data) as mview:
			return _parse(mview)
	except HprofError:
		# _parse failed
		raise
	except Exception as e:
		# we failed before calling _parse
		failures.append(('bytes-like?', e))

	# can it be mmapped?
	from mmap import mmap, ACCESS_READ
	from io import BufferedReader
	if isinstance(data, BufferedReader):
		import os
		try:
			fno = data.fileno()
			fsize = os.fstat(fno).st_size
			with mmap(fno, fsize, access=ACCESS_READ) as mapped:
				with memoryview(mapped) as mview:
					return _parse(mview)
		except HprofError:
			raise

	# can it be read?
	try:
		from tempfile import TemporaryFile
		with TemporaryFile() as f:
			buf = bytearray(8192)
			fsize = 0
			while True:
				nread = data.readinto(buf)
				if not nread:
					break
				fsize += nread
				f.write(buf[:nread])
			f.flush()
			with mmap(f.fileno(), fsize) as mapped:
				with memoryview(mapped) as mview:
					return _parse(mview)
	except HprofError:
		raise
	except Exception as e:
		failures.append(('tmpfile?', e))

	raise TypeError('cannot handle `data` arg', data, failures)



class PrimitiveReader(object):
	def __init__(self, bytes):
		self._bytes = bytes
		self._pos = 0


	def bytes(self, nbytes):
		''' read n bytes of data '''
		out = self._bytes[self._pos : self._pos + nbytes]
		if len(out) != nbytes:
			raise UnexpectedEof('tried to read %d bytes, got %d' % (nbytes, len(out)))
		self._pos += nbytes
		return out

	def ascii(self):
		''' read a zero-terminated ASCII string '''
		out = []
		while True:
			byte = self.bytes(1)
			if byte == b'\0':
				return b''.join(out).decode('ascii')
			out.append(byte)

	def u(self, nbytes):
		''' read an n-byte (big-endian) unsigned number '''
		out = 0
		for b in self.bytes(nbytes):
			out = (out << 8) + b
		return out

record_parsers = {
}

def _parse(data):
	try:
		return _parse_hprof(data)
	except HprofError:
		raise
	except Exception as e:
		raise UnhandledError() from e

def _parse_hprof(bstream):
	reader = PrimitiveReader(bstream)
	hdr = reader.ascii()
	if not hdr == 'JAVA PROFILE 1.0.1':
		raise FormatError('unknown header "%s"' % hdr)
	hf = HprofFile()
	hf.idsize = reader.idsize = reader.u(4)
	reader.u(8) # timestamp; ignore.
	while True:
		try:
			rtype = reader.u(1)
		except UnexpectedEof:
			break # not unexpected.
		micros = reader.u(4)
		datasize = reader.u(4)
		data = reader.bytes(datasize)
		try:
			parser = record_parsers[rtype]
		except KeyError as e:
			parser = lambda data: record.Unhandled(rtype)
		r = parser(data)
		hf.records.append(r)
	return hf

