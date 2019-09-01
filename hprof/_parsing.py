import struct
import codecs

from .error import *
from . import callstack
from . import heap
from . import jtype

class HprofFile(object):
	def __init__(self):
		self.unhandled = {} # record tag -> count
		self.names = {0: None}
		self.stackframes = {}
		self.threads = {0: None}
		self.stacktraces = {}
		self.classloads = {} # by serial
		self.classloads_by_id = {}
		self.heaps = []


class ClassLoad(object):
	__slots__ = ('class_id', 'class_name', 'stacktrace')

	def __str__(self):
		return 'ClassLoad<clsid=0x%x name=%s trace=%s>' % (self.class_id, self.class_name, repr(self.stacktrace))

	def __repr__(self):
		return str(self)

	def __eq__(self, other):
		try:
			return (self.class_id == other.class_id
			    and self.class_name is other.class_name
			    and self.stacktrace is other.stacktrace)
		except AttributeError:
			return False


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
	except (HprofError, BufferError):
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
		fno = data.fileno()
		fsize = os.fstat(fno).st_size
		with mmap(fno, fsize, access=ACCESS_READ) as mapped:
			with memoryview(mapped) as mview:
				return _parse(mview)

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
	except BufferError as e:
		raise
	except Exception as e:
		prev = e
		while prev is not None:
			if isinstance(prev, HprofError):
				raise e
			prev = prev.__context__
		failures.append(('tmpfile?', e))

	raise TypeError('cannot handle `data` arg', data, *failures)


def hprof_mutf8_error_handler(err):
	obj = err.object
	ix = err.start
	if obj[ix:ix+2] == b'\xc0\x80':
		# special handling for encoded null, because I'm lazy
		return '\0', ix + 2
	elif len(obj) >= ix + 6:
		# try to decode as a surrogate pair
		obj = obj[ix:ix+6]
		if ((obj[0] & 0xf0) == 0xe0
		and (obj[1] & 0xc0) == 0x80
		and (obj[2] & 0xc0) == 0x80
		and (obj[3] & 0xf0) == 0xe0
		and (obj[4] & 0xc0) == 0x80
		and (obj[5] & 0xc0) == 0x80):
			raw = (
				(obj[0] << 4 & 0xf0) + (obj[1] >> 2 & 0x0f),
				(obj[1] << 6 & 0xc0) + (obj[2]      & 0x3f),
				(obj[3] << 4 & 0xf0) + (obj[4] >> 2 & 0x0f),
				(obj[4] << 6 & 0xc0) + (obj[5]      & 0x3f),
			)
			return bytes(raw).decode('utf-16-be'), ix + 6
	raise err
codecs.register_error('hprof-mutf8', hprof_mutf8_error_handler)


class PrimitiveReader(object):
	def __init__(self, bytes, idsize):
		self._bytes = bytes
		self._pos = 0
		self._idsize = idsize

	@property
	def remaining(self):
		return len(self._bytes) - self._pos

	def bytes(self, nbytes):
		''' read n bytes of data '''
		out = self._bytes[self._pos : self._pos + nbytes]
		if len(out) != nbytes:
			raise UnexpectedEof('tried to read %d bytes, got %d' % (nbytes, len(out)))
		self._pos += nbytes
		return out

	def ascii(self):
		''' read a zero-terminated ASCII string '''
		end = self._pos
		bs = self._bytes
		N = len(bs)
		while end < N and bs[end] != 0:
			end += 1
		if end == N:
			raise UnexpectedEof('unterminated ascii string')
		try:
			out = str(bs[self._pos : end], 'ascii')
		except UnicodeError as e:
			raise FormatError() from e
		self._pos = end + 1
		return out

	def utf8(self, nbytes):
		''' read n bytes, interpret as (m)UTF-8 '''
		raw = self._bytes[self._pos : self._pos + nbytes]
		if len(raw) != nbytes:
			raise UnexpectedEof('tried to read %d bytes, got %d' % (nbytes, len(raw)))
		try:
			out = str(raw, 'utf8', 'hprof-mutf8')
		except UnicodeError as e:
			raise FormatError() from e
		self._pos += nbytes
		return out

	def id(self):
		out = 0
		bs = self._bytes
		nbytes = self._idsize
		try:
			for ix in range(self._pos, self._pos + nbytes):
				out = (out << 8) + bs[ix]
		except IndexError:
			fmt = 'tried to read %d-byte id; only %d bytes available'
			raise UnexpectedEof(fmt % (nbytes, self.remaining))
		self._pos += nbytes
		return out

	def u1(self):
		try:
			out = self._bytes[self._pos]
		except IndexError as e:
			raise UnexpectedEof() from e
		self._pos += 1
		return out

	def u2(self):
		bs = self._bytes
		pos = self._pos
		try:
			out = ((bs[pos + 0] << 8)
			     + (bs[pos + 1]))
		except IndexError as e:
			raise UnexpectedEof() from e
		self._pos += 2
		return out

	def u4(self):
		bs = self._bytes
		pos = self._pos
		try:
			out = ((bs[pos + 0] << 24)
			     + (bs[pos + 1] << 16)
			     + (bs[pos + 2] <<  8)
			     + (bs[pos + 3]))
		except IndexError as e:
			raise UnexpectedEof() from e
		self._pos += 4
		return out

	def u8(self):
		bs = self._bytes
		pos = self._pos
		try:
			out = ((bs[pos + 0] << 56)
			     + (bs[pos + 1] << 48)
			     + (bs[pos + 2] << 40)
			     + (bs[pos + 3] << 32)
			     + (bs[pos + 4] << 24)
			     + (bs[pos + 5] << 16)
			     + (bs[pos + 6] <<  8)
			     + (bs[pos + 7]))
		except IndexError as e:
			raise UnexpectedEof() from e
		self._pos += 8
		return out

	def i1(self):
		try:
			out = (self._bytes[self._pos] ^ 0x80) - 0x80
		except IndexError as e:
			raise UnexpectedEof() from e
		self._pos += 1
		return out

	def i2(self):
		bs = self._bytes
		pos = self._pos
		try:
			out = ((bs[pos + 0] << 8)
			     + (bs[pos + 1]))
		except IndexError as e:
			raise UnexpectedEof() from e
		out = (out ^ 0x8000) - 0x8000
		self._pos += 2
		return out

	def i4(self):
		bs = self._bytes
		pos = self._pos
		try:
			out = ((bs[pos + 0] << 24)
			     + (bs[pos + 1] << 16)
			     + (bs[pos + 2] <<  8)
			     + (bs[pos + 3]))
		except IndexError as e:
			raise UnexpectedEof() from e
		out = (out ^ 0x80000000) - 0x80000000
		self._pos += 4
		return out

	def i8(self):
		bs = self._bytes
		pos = self._pos
		try:
			out = ((bs[pos + 0] << 56)
			     + (bs[pos + 1] << 48)
			     + (bs[pos + 2] << 40)
			     + (bs[pos + 3] << 32)
			     + (bs[pos + 4] << 24)
			     + (bs[pos + 5] << 16)
			     + (bs[pos + 6] <<  8)
			     + (bs[pos + 7]))
		except IndexError as e:
			raise UnexpectedEof() from e
		out = (out ^ 0x8000000000000000) - 0x8000000000000000
		self._pos += 8
		return out

	def jtype(self):
		typeval = self.u1()
		try:
			return jtype(typeval)
		except ValueError as e:
			raise FormatError() from e

	def jboolean(self):
		return self.u1() != 0

	def jchar(self):
		return codecs.decode(self.bytes(2), 'utf-16-be', 'surrogatepass')

	def jfloat(self):
		v, = struct.unpack('>f', self.bytes(4))
		return v

	def jdouble(self):
		v, = struct.unpack('>d', self.bytes(8))
		return v

jtype.object.read  = PrimitiveReader.id
jtype.boolean.read = PrimitiveReader.jboolean
jtype.boolean.size = 1
jtype.char.read    = PrimitiveReader.jchar
jtype.char.size    = 2
jtype.float.read   = PrimitiveReader.jfloat
jtype.float.size   = 4
jtype.double.read  = PrimitiveReader.jdouble
jtype.double.size  = 8
jtype.byte.read    = PrimitiveReader.i1
jtype.byte.size    = 1
jtype.short.read   = PrimitiveReader.i2
jtype.short.size   = 2
jtype.int.read     = PrimitiveReader.i4
jtype.int.size     = 4
jtype.long.read    = PrimitiveReader.i8
jtype.long.size    = 8


record_parsers = {}

def parse_name_record(hf, reader):
	nameid = reader.id()
	name = reader.utf8(reader.remaining)
	if nameid in hf.names:
		raise FormatError('duplicate name id 0x%x' % nameid)
	hf.names[nameid] = name
record_parsers[0x01] = parse_name_record

def parse_class_load_record(hf, reader):
	serial = reader.u4()
	clsid  = reader.id()
	load = ClassLoad()
	load.class_id = clsid
	load.stacktrace = reader.u4() # resolve later
	load.class_name = hf.names[reader.id()]
	if serial in hf.classloads:
		raise FormatError('duplicate class load serial 0x%x' % serial, hf.classloads[serial], load)
	if clsid in hf.classloads_by_id:
		other = hf.classloads_by_id[clsid]
		if load == other:
			# XXX: This is apparently something that can happen. I don't know what it means.
			#      If they're identical, let's just join them for now.
			load = other
		else:
			raise FormatError('duplicate class load id 0x%x' % clsid, other, load)
	hf.classloads[serial] = load
	hf.classloads_by_id[clsid] = load
record_parsers[0x02] = parse_class_load_record

def parse_stack_frame_record(hf, reader):
	frame = callstack.Frame()
	fid = reader.id()
	frame.method     = hf.names[reader.id()]
	frame.signature  = hf.names[reader.id()]
	frame.sourcefile = hf.names[reader.id()]
	frame.class_name = hf.classloads[reader.u4()].class_name
	frame.line       = reader.i4()
	if fid in hf.stackframes:
		raise FormatError('duplicate stack frame id 0x%x' % fid)
	hf.stackframes[fid] = frame
record_parsers[0x04] = parse_stack_frame_record

def parse_stack_trace_record(hf, reader):
	trace = callstack.Trace()
	serial = reader.u4()
	thread = reader.u4()
	if thread not in hf.threads:
		hf.threads[thread] = 'dummy thread' # TODO: use a real thread instance
	trace.thread = hf.threads[thread]
	nframes = reader.u4()
	for ix in range(nframes):
		fid = reader.id()
		trace.append(hf.stackframes[fid])
	if serial in hf.stacktraces:
		raise FormatError('duplicate stack trace serial 0x%x' % serial)
	hf.stacktraces[serial] = trace
record_parsers[0x05] = parse_stack_trace_record

def parse_heap_record(hf, reader):
	from . import _heap_parsing
	out = heap.Heap()
	_heap_parsing.parse_heap(out, reader)
	_heap_parsing.resolve_heap_references(out)
	hf.heaps.append(out)
record_parsers[0x0c] = parse_heap_record

def _parse(data):
	try:
		return _parse_hprof(data)
	except HprofError:
		raise
	except Exception as e:
		raise UnhandledError() from e

def _parse_hprof(mview):
	reader = PrimitiveReader(mview, None)
	hdr = reader.ascii()
	if not hdr == 'JAVA PROFILE 1.0.1':
		raise FormatError('unknown header "%s"' % hdr)
	hf = HprofFile()
	idsize = reader._idsize = reader.u4()
	reader.u8() # timestamp; ignore.
	while True:
		try:
			rtype = reader.u1()
		except UnexpectedEof:
			break # not unexpected.
		micros = reader.u4()
		datasize = reader.u4()
		data = reader.bytes(datasize)
		try:
			parser = record_parsers[rtype]
		except KeyError as e:
			hf.unhandled[rtype] = hf.unhandled.get(rtype, 0) + 1
		else:
			parser(hf, PrimitiveReader(data, idsize))
	_resolve_references(hf)
	return hf

def _resolve_references(hf):
	''' Some objects can have forward references. In those cases, we've saved
	a serial or id -- now is the time to replace them with real references.'''
	for load in hf.classloads.values():
		try:
			if type(load.stacktrace) is int:
				load.stacktrace = hf.stacktraces[load.stacktrace]
		except KeyError as e:
			msg = 'ClassLoad of %s refers to stacktrace 0x%x, which cannot be found'
			raise FormatError(msg % (load.class_name, load.stacktrace)) from e
