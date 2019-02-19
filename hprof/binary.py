#!/usr/bin/env python3
#coding=utf8

from datetime import datetime
from mmap import mmap, MAP_PRIVATE, PROT_READ

import builtins
import struct

from .heapdump import Dump
from .errors import *
from .offset import offset
from .record import Record, HeapDumpSegment, HeapDumpEnd, Utf8
from .types import JavaType

def open(path):
	return HprofFile(path)

def untuple(t):
	assert len(t) == 1
	return t[0]

class HprofFile(object):
	def __init__(self, data):
		''' data may be a file path or just plain bytes. '''
		if type(data) is bytes:
			self._f = None
			self._data = data
		elif type(data) is str:
			self._f = builtins.open(data, 'rb')
			self._data = mmap(self._f.fileno(), 0, MAP_PRIVATE, PROT_READ);
		else:
			raise TypeError(type(data))

		s = self.stream()
		ident = s.read_bytes(13)
		if ident != b'JAVA PROFILE ':
			raise FileFormatError('bad header: expected JAVA PROFILE, but found %s' % repr(ident))
		version = s.read_ascii()
		if version != '1.0.3':
			raise FileFormatError('bad version: expected 1.0.3, but found %s' % version)

		self.idsize = s.read_uint()
		timestamp_ms = (s.read_uint() << 32) + s.read_uint()
		self.starttime = datetime.fromtimestamp(timestamp_ms / 1000)
		self._first_record_addr = s.addr
		self._dumps = None

		self._names = {}
		for r in self.records():
			if type(r) is Utf8:
				nameid = r.id
				if nameid in self._names:
					old = self._names[nameid]
					raise FileFormatError(
							'duplicate name id 0x%x: "%s" at 0x%x and "%s" at 0x%x'
							% (nameid, old.str, old.addr, r.str, r.addr))
				self._names[nameid] = r

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

	def records(self):
		s = self.stream(self._first_record_addr)
		while True:
			start = s.addr
			try:
				tag = s.read_byte()
			except EofError:
				break # alright, everything lined up nicely!
			r = Record.create(self, start)
			s.skip(len(r) - 1) # skip the rest of the record; -1 because we already read the tag.
			yield r

	def dumps(self):
		if self._dumps is None:
			curdump = None
			dumps = []
			for r in self.records():
				if type(r) is HeapDumpSegment:
					if curdump is None:
						curdump = Dump(self)
						dumps.append(curdump)
					curdump._add_segment(r)
				elif type(r) is HeapDumpEnd:
					if curdump is None:
						dumps.append(Dump(self))
					curdump = None
			self._dumps = tuple(dumps)
		yield from self._dumps

	def close(self):
		if self._data is not None:
			if type(self._data) is mmap:
				self._data.close()
			self._data = None
		if self._f is not None:
			self._f.close()
			self._f = None

	def stream(self, start_addr=0):
		return HprofStream(self, start_addr)

	def __getattr__(self, name):
		''' return a wrapper for a single read through a Stream, if such a function exists. '''
		if not hasattr(HprofStream, name):
			raise AttributeError(name)
		def stream_wrapper(*args, **kwargs):
			s = self.stream(0)
			f = getattr(s, name)
			if len(args) < 1:
				raise TypeError('random reads must supply a start address')
			s.skip(args[0])
			return f(*args[1:], **kwargs)
		return stream_wrapper

	def name(self, nameid):
		try:
			return self._names[nameid]
		except KeyError:
			raise RefError('name', nameid)

def _bytes_to_int(bytes):
	i = 0
	for b in bytes:
		i = (i << 8) + b
	return i

def _bytes_to_bool(bytes):
	b, = bytes
	if b == 0:
		return False
	elif b == 1:
		return True
	else:
		raise FileFormatError('invalid boolean value 0x%x' % b)

def _bytes_to_jtype(bytes):
	b, = bytes
	try:
		return JavaType(b)
	except ValueError:
		raise FileFormatError('invalid JavaType: 0x%x' % b)

def _bytes_to_char(bytes):
	return bytes.decode('utf-16-be')

class HprofStream(object):
	def __init__(self, hf, startaddr):
		self._addr = 0
		self._hf = hf
		self.jump_to(startaddr)

	@property
	def addr(self):
		return self._addr

	def skip(self, nbytes):
		self.jump_to(self._addr + nbytes)

	def jump_to(self, addr):
		if isinstance(addr, offset):
			addr = addr.flatten(self._hf.idsize)
		if addr < 0 or addr > len(self._hf._data):
			raise EofError('tried to jump to %d, but file size is %d' % (addr, len(self._hf._data)))
		self._addr = addr

	def _consume_bytes(self, nbytes, conversion):
		if isinstance(nbytes, offset):
			nbytes = nbytes.flatten(self._hf.idsize)
		start = self._addr
		length = len(self._hf._data)
		if nbytes is not None:
			if nbytes < 0:
				raise ValueError('invalid nbytes', nbytes)
			end = start + nbytes
			if end > length:
				raise EofError('tried to read bytes %d:%d, but file size is %d' % (start, end, length))
			next = end
		else:
			end = start
			while end < length:
				if self._hf._data[end] == 0:
					break
				end += 1
			else:
				raise EofError('tried to read from %d to null termination, but exceeded file size %d' % (start, length))
			next = end + 1 # consume the zero byte as well
		out = conversion(self._hf._data[start:end])
		self._addr = next # conversion succeeded; consume the bytes.
		return out

	def read_bytes(self, nbytes):
		''' Read a byte string of nbytes. '''
		return self._consume_bytes(nbytes, lambda b: b)

	def read_ascii(self, nbytes=None):
		''' Read an ascii string of nbytes. If nbytes is None, read until a zero byte is found. '''
		return self._consume_bytes(nbytes, lambda b: b.decode('ascii'))

	def read_utf8(self, nbytes):
		''' Read an utf8 string of nbytes. Note: byte count, not character count! '''
		return self._consume_bytes(nbytes, lambda b: b.decode('utf8'))

	def read_jtype(self):
		return self._consume_bytes(1, _bytes_to_jtype)

	def read_jvalue(self, jtype):
		readers = {
			JavaType.object:  self.read_id,
			JavaType.boolean: self.read_boolean,
			JavaType.byte:    self.read_byte,
			JavaType.char:    self.read_char,
			JavaType.short:   self.read_short,
			JavaType.int:     self.read_int,
			JavaType.long:    self.read_long,
			JavaType.float:   self.read_float,
			JavaType.double:  self.read_double,
		}
		try:
			rfun = readers[jtype]
		except KeyError:
			raise Error('unhandled (or invalid) JavaType: %s' % jtype)
		return rfun()

	def _read_value(self, fmt):
		fmt = '>' + fmt
		n = struct.calcsize(fmt)
		return self._consume_bytes(n, lambda b: untuple(struct.unpack(fmt, b)))

	def read_char(self):
		return self._consume_bytes(2, _bytes_to_char)

	def read_byte(self):
		return self._read_value('B')

	def read_uint(self):
		return self._read_value('I')

	def read_int(self):
		return self._read_value('i')

	def read_ushort(self):
		return self._read_value('H')

	def read_short(self):
		return self._read_value('h')

	def read_boolean(self):
		return self._consume_bytes(1, _bytes_to_bool)

	def read_id(self):
		return self._consume_bytes(self._hf.idsize, _bytes_to_int)

	def read_float(self):
		return self._read_value('f')

	def read_double(self):
		return self._read_value('d')

	def read_long(self):
		return self._read_value('q')
