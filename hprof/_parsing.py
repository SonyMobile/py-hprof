# Copyright (C) 2019 Snild Dolkow
# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

'''
Parses hprof files' main record stream.
'''

import struct
import codecs
import gc

from contextlib import contextmanager
from enum import Enum

from .error import FormatError, HprofError, UnexpectedEof, UnhandledError
from .heap import Heap
from . import callstack
from . import _special_cases

class HprofFile(object):
	''' Your hprof file. Must stay open as long as you have references to any
	heaps or heap objects, or you may get nasty BufferErrors.
	'''

	def __init__(self):
		self._context = None
		self.unhandled = {} # record tag -> count
		self.names = {0: None}
		self.stackframes = {}
		self.threads = {0: None}
		self.stacktraces = {}
		self.classloads = {} # by serial
		self.classloads_by_id = {}
		self.heaps = []
		self._pending_heap = None

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, tb):
		ctx = self._context
		if ctx is not None:
			self._context = None
			# drop the heaps and force a GC to eliminate refs into file mappings
			self.heaps = None
			gc.collect()
			return ctx.__exit__(exc_type, exc_val, tb)

	def close(self):
		''' Close the file. '''
		self.__exit__(None, None, None)

	def __del__(self):
		self.close()

class ClassLoad(object):
	''' A record detailing parameters of a loaded class. Not to be confused with
	a class instance, which can be found in the heap dump using class_id. '''

	__slots__ = ('class_id', 'class_name', 'stacktrace')

	def __init__(self, clsid, clsname, strace):
		self.class_id = clsid
		self.class_name = clsname
		self.stacktrace = strace

	def __str__(self):
		return 'ClassLoad<clsid=0x%x name=%s trace=%s>' % (self.class_id, self.class_name, repr(self.stacktrace))

	def __repr__(self):
		return str(self)

	def __eq__(self, other):
		return (self.class_id == other.class_id
		    and self.class_name == other.class_name
		    and self.stacktrace == other.stacktrace)


def open(path, progress_callback=None): # pylint: disable=redefined-builtin
	''' Open an hprof file.

	Accepts .bz2, .gz, and .xz compressed hprof files for your convenience.

	progress_callback, if supplied, will be called periodically with three
	parameters: (label, done, total). `label` is a string describing the current
	action. `done` and `total` are ints describing the progress of that action.
	`done` and `total` may be `None`.
	'''
	hf = HprofFile()
	hf._context = _open_cm(hf, path, progress_callback)
	hf._context.__enter__()
	return hf

@contextmanager
def _open_cm(hf, path, progress_callback):
	if progress_callback:
		progress_callback('opening', None, None)
	if path.endswith('.bz2'):
		import bz2
		with bz2.open(path, 'rb') as f:
			with _parse_cm(hf, f, progress_callback):
				yield hf
	elif path.endswith('.gz'):
		import gzip
		with gzip.open(path, 'rb') as f:
			with _parse_cm(hf, f, progress_callback):
				yield hf
	elif path.endswith('.xz'):
		import lzma
		with lzma.open(path, 'rb') as f:
			with _parse_cm(hf, f, progress_callback):
				yield hf
	else:
		import builtins
		with builtins.open(path, 'rb') as f:
			with _parse_cm(hf, f, progress_callback):
				yield hf

def parse(data, progress_callback=None):
	''' Like `open()`, but when you already have the data in memory. '''
	hf = HprofFile()
	hf._context = _parse_cm(hf, data, progress_callback)
	hf._context.__enter__()
	return hf

@contextmanager
def _parse_cm(hf, data, progress_callback):
	failures = []

	# is it a bytes-like?
	try:
		with memoryview(data) as mview:
			_parse(hf, mview, progress_callback)
			yield hf
			return
	except (HprofError, BufferError):
		# _parse failed
		raise
	except Exception as e: # pylint: disable=broad-except
		# we failed before calling _parse
		failures.append(('bytes-like?', e))

	# can it be mmapped?
	from mmap import mmap, ACCESS_READ
	from io import BufferedReader
	import os
	if isinstance(data, BufferedReader):
		fno = data.fileno()
		fsize = os.fstat(fno).st_size
		with mmap(fno, fsize, access=ACCESS_READ) as mapped:
			with memoryview(mapped) as mview:
				_parse(hf, mview, progress_callback)
				yield hf
				return

	# can it be read?
	try:
		from tempfile import TemporaryFile
		from io import FileIO
		underlying_file = FileIO(data.fileno(), closefd=False)
		insize = os.fstat(underlying_file.fileno()).st_size
		with TemporaryFile() as f:
			buf = bytearray(256 * 1024)
			fsize = 0
			while True:
				if progress_callback:
					progress_callback('extracting', min(underlying_file.tell(), insize-1), insize)
				nread = data.readinto(buf)
				if not nread:
					break
				fsize += nread
				f.write(buf[:nread])
			f.flush()
			if progress_callback:
				progress_callback('extracting', insize, insize)
			with mmap(f.fileno(), fsize) as mapped:
				with memoryview(mapped) as mview:
					_parse(hf, mview, progress_callback)
					yield hf
					return
	except BufferError as e:
		raise
	except Exception as e: # pylint: disable=broad-except
		prev = e
		while prev is not None:
			if isinstance(prev, HprofError):
				raise e
			prev = prev.__context__ # pylint: disable=redefined-variable-type
		failures.append(('tmpfile?', e))

	raise TypeError('cannot handle `data` arg', data, *failures)


def hprof_mutf8_error_handler(err):
	''' Java VMs are fond of their "modified UTF-8" string encoding. Most
	notably, the largest code points are double-encoded. It's super annoying.

	https://source.android.com/devices/tech/dalvik/dex-format#mutf-8

	This error handler fixes up the parts of the decoding process that python's
	standard utf-8 decoder can't handle.
	'''

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
	''' Supports linear reads of various types.

	One source of complications is that different hprof files may use different
	byte counts for the "id" type, which is used for e.g. object references.
	'''
	def __init__(self, input_bytes, idsize):
		self._bytes = input_bytes
		self._pos = 0
		self._set_idsize(idsize)

	def _set_idsize(self, idsize):
		self._idsize = idsize
		if idsize == 8:
			self.id = self.u8 # pylint: disable=invalid-name
		elif idsize == 4:
			self.id = self.u4 # pylint: disable=invalid-name
		else:
			self.id = self._generic_id # pylint: disable=invalid-name

	def _indirect_id(self):
		return self.id()

	@property
	def remaining(self):
		''' How many bytes are left to read? '''
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
		n = len(bs)
		while end < n and bs[end] != 0:
			end += 1
		if end == n:
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

	def _generic_id(self):
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

	def u1(self): # pylint: disable=invalid-name
		''' Read an unsigned 8-bit value. '''
		try:
			out = self._bytes[self._pos]
		except IndexError as e:
			raise UnexpectedEof() from e
		self._pos += 1
		return out

	def u2(self): # pylint: disable=invalid-name
		''' Read an unsigned 16-bit value. '''
		bs = self._bytes
		pos = self._pos
		try:
			out = ((bs[pos + 0] << 8)
			     + (bs[pos + 1]))
		except IndexError as e:
			raise UnexpectedEof() from e
		self._pos += 2
		return out

	def u4(self): # pylint: disable=invalid-name
		''' Read an unsigned 32-bit value. '''
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

	def u8(self): # pylint: disable=invalid-name
		''' Read an unsigned 64-bit value. '''
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

	def i1(self): # pylint: disable=invalid-name
		''' Read a signed 8-bit value. '''
		try:
			out = (self._bytes[self._pos] ^ 0x80) - 0x80
		except IndexError as e:
			raise UnexpectedEof() from e
		self._pos += 1
		return out

	def i2(self): # pylint: disable=invalid-name
		''' Read a signed 16-bit value. '''
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

	def i4(self): # pylint: disable=invalid-name
		''' Read a signed 32-bit value. '''
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

	def i8(self): # pylint: disable=invalid-name
		''' Read a signed 64-bit value. '''
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
		''' Read a `hprof.jtype` value, as in "which type?". '''
		typeval = self.u1()
		try:
			return jtype(typeval)
		except ValueError as e:
			raise FormatError() from e

	def jboolean(self):
		''' Read a java boolean value. '''
		return self.u1() != 0

	def jchar(self):
		''' Read a java (16-bit) char value. Almost utf16. '''
		return codecs.decode(self.bytes(2), 'utf-16-be', 'surrogatepass')

	def jfloat(self):
		''' Read a java float value. '''
		v, = struct.unpack('>f', self.bytes(4))
		return v

	def jdouble(self):
		''' Read a java double value. '''
		v, = struct.unpack('>d', self.bytes(8))
		return v

class jtype(Enum): # pylint: disable=invalid-name
	''' The various variable types supported by hprof files.

	Note that the format makes no distinction between different object reference
	types. This means that it's impossible to know the declared type of a
	non-primitive variable.
	'''

	object = 2
	boolean = 4
	char = 5
	float = 6
	double = 7
	byte = 8
	short = 9
	int = 10
	long = 11

jtype.object.read  = PrimitiveReader._indirect_id
jtype.boolean.read = PrimitiveReader.jboolean
jtype.boolean.size = 1
jtype.boolean.packfmt = '?'
jtype.char.read    = PrimitiveReader.jchar
jtype.char.size    = 2
jtype.char.packfmt = 'c'
jtype.float.read   = PrimitiveReader.jfloat
jtype.float.size   = 4
jtype.float.packfmt = 'f'
jtype.double.read  = PrimitiveReader.jdouble
jtype.double.size  = 8
jtype.double.packfmt = 'd'
jtype.byte.read    = PrimitiveReader.i1
jtype.byte.size    = 1
jtype.byte.packfmt = 'b'
jtype.short.read   = PrimitiveReader.i2
jtype.short.size   = 2
jtype.short.packfmt = 'h'
jtype.int.read     = PrimitiveReader.i4
jtype.int.size     = 4
jtype.int.packfmt  = 'i'
jtype.long.read    = PrimitiveReader.i8
jtype.long.size    = 8
jtype.long.packfmt = 'q'


RECORD_PARSERS = {}

def parse_name_record(hf, reader, progresscb):
	''' Parse an hprof name record.

	These will be referenced in various other records for things like class,
	field, and method names.
	'''
	del progresscb # unused
	nameid = reader.id()
	name = reader.utf8(reader.remaining)
	if nameid in hf.names:
		raise FormatError('duplicate name id 0x%x' % nameid)
	hf.names[nameid] = name
RECORD_PARSERS[0x01] = parse_name_record

def parse_class_load_record(hf, reader, progresscb):
	''' See `ClassLoad`. '''
	del progresscb # unused
	serial = reader.u4()
	clsid  = reader.id()
	strace = reader.u4() # resolve later
	clsname= hf.names[reader.id()]
	load = ClassLoad(clsid, clsname, strace)
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
RECORD_PARSERS[0x02] = parse_class_load_record

def parse_stack_frame_record(hf, reader, progresscb):
	''' Parse information about a single stack frame. '''
	del progresscb # unused
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
RECORD_PARSERS[0x04] = parse_stack_frame_record

def parse_stack_trace_record(hf, reader, progresscb):
	''' Parse information about a stack trace. '''
	del progresscb # unused
	trace = callstack.Trace()
	serial = reader.u4()
	thread = reader.u4()
	if thread not in hf.threads:
		hf.threads[thread] = 'dummy thread' # TODO: use a real thread instance
	trace.thread = hf.threads[thread]
	nframes = reader.u4()
	for _ in range(nframes):
		fid = reader.id()
		trace.append(hf.stackframes[fid])
	if serial in hf.stacktraces:
		raise FormatError('duplicate stack trace serial 0x%x' % serial)
	hf.stacktraces[serial] = trace
RECORD_PARSERS[0x05] = parse_stack_trace_record

def parse_heap_record(hf, reader, progresscb):
	''' Parse a heap dump record. This is what gives us heaps to inspect. '''
	if hf._pending_heap is not None:
		raise FormatError('found non-segmented heap, but have unfinished segmented heap')
	parse_heap_record_segment(hf, reader, progresscb)
	parse_heap_record_seg_end(hf, reader, progresscb)
RECORD_PARSERS[0x0c] = parse_heap_record

def parse_heap_record_segment(hf, reader, progresscb):
	''' Like `parse_heap_record()`, but when the heap is segmented across
	multiple records.
	'''
	from . import _heap_parsing
	if hf._pending_heap is None:
		hf._pending_heap = Heap()
	_heap_parsing.parse_heap(hf, hf._pending_heap, reader, progresscb)
RECORD_PARSERS[0x1c] = parse_heap_record_segment

def parse_heap_record_seg_end(hf, reader, progresscb):
	''' Ends a segmented heap. '''
	del reader, progresscb # unused
	if hf._pending_heap is None:
		raise FormatError('no pending heap to end')
	hf.heaps.append(hf._pending_heap)
	hf._pending_heap = None
RECORD_PARSERS[0x2c] = parse_heap_record_seg_end

def _parse(hf, data, progresscb):
	try:
		_parse_hprof(hf, data, progresscb)
	except HprofError:
		raise
	except Exception as e:
		raise UnhandledError() from e

def _parse_hprof(hf, mview, progresscb):
	reader = PrimitiveReader(mview, None)
	if progresscb:
		progresscb('parsing', 0, len(mview))
	hdr = reader.ascii()
	if hdr not in ('JAVA PROFILE 1.0.1', 'JAVA PROFILE 1.0.2', 'JAVA PROFILE 1.0.3'):
		raise FormatError('unknown header "%s"' % hdr)
	idsize = reader.u4()
	reader._set_idsize(idsize)
	reader.u8() # timestamp; ignore.
	lastreport = -1<<32
	def innerprogress(pos):
		''' progress helper sent to record parsers '''
		progresscb('parsing', innerprogress.base + pos, len(mview))
	if not progresscb:
		innerprogress = None
	while True:
		try:
			rtype = reader.u1()
		except UnexpectedEof:
			break # not unexpected.
		if progresscb:
			innerprogress.base = reader._pos
			if reader._pos - lastreport >= 1<<20:
				lastreport = reader._pos
				progresscb('parsing', reader._pos, len(mview))
		_ = reader.u4() # microsecond timestamp
		datasize = reader.u4()
		data = reader.bytes(datasize)
		try:
			parser = RECORD_PARSERS[rtype]
		except KeyError:
			hf.unhandled[rtype] = hf.unhandled.get(rtype, 0) + 1
		else:
			parser(hf, PrimitiveReader(data, idsize), innerprogress)
	if progresscb:
		progresscb('parsing', len(mview), len(mview))
	_instantiate(hf, reader._idsize, progresscb)
	_resolve_references(hf, progresscb)
	_special_cases.setup_builtins(hf)

def _instantiate(hf, idsize, progresscb):
	from . import _heap_parsing
	for heapix, heap in enumerate(hf.heaps, start=1):
		if heap._deferred_classes:
			raise FormatError('some class dumps never found their super class', heap._deferred_classes)

		def remaining():
			''' how many objects are left to instantiate? '''
			# pylint: disable=cell-var-from-loop
			return (
				len(heap._deferred_objects)
				+ len(heap._deferred_objarrays)
				+ len(heap._deferred_primarrays)
			)
		total = remaining()
		label = 'instantiating heap %d/%d' % (heapix, len(hf.heaps))
		if progresscb:
			def localprogress(n):
				''' progress helper '''
				# pylint: disable=cell-var-from-loop
				progresscb(label, done + n, total)
		else:
			def localprogress(n):
				''' dummy progress callback '''
				del n # unused

		done = 0
		_heap_parsing.create_instances(heap, idsize, localprogress)
		done = total - remaining()
		_heap_parsing.create_objarrays(heap, localprogress)
		done = total - remaining()
		_heap_parsing.create_primarrays(heap, localprogress)
		done = total - remaining()
		localprogress(0)

def _resolve_references(hf, progresscb):
	''' Some objects can have forward references. In those cases, we've saved
	a serial or id -- now is the time to replace them with real references.'''
	if progresscb:
		progresscb('resolving stacktraces', None, None)
	for load in hf.classloads.values():
		try:
			if isinstance(load.stacktrace, int):
				load.stacktrace = hf.stacktraces[load.stacktrace]
		except KeyError as e:
			msg = 'ClassLoad of %s refers to stacktrace 0x%x, which cannot be found'
			raise FormatError(msg % (load.class_name, load.stacktrace)) from e
	from . import _heap_parsing
	if hf._pending_heap is not None:
		raise FormatError('unfinished segmented heap')
	for heapix, heap in enumerate(hf.heaps, start=1):
		n = len(heap)
		label = 'resolving heap %d/%d' % (heapix, len(hf.heaps))
		def innerprogress(pos):
			''' progress helper '''
			# pylint: disable=cell-var-from-loop
			progresscb(label, pos, n)
		if not progresscb:
			innerprogress = None
		_heap_parsing.resolve_heap_references(heap, innerprogress)
