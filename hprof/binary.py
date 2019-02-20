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

		ident = self.read_bytes(0, 13)
		if ident != b'JAVA PROFILE ':
			raise FileFormatError('bad header: expected JAVA PROFILE, but found %s' % repr(ident))
		version = self.read_ascii(13)
		if version != '1.0.3':
			raise FileFormatError('bad version: expected 1.0.3, but found %s' % version)
		base = 13 + len(version) + 1

		self.idsize = self.read_uint(base)
		timestamp_ms = (self.read_uint(base + 4) << 32) + self.read_uint(base + 8)
		self.starttime = datetime.fromtimestamp(timestamp_ms / 1000)
		self._first_record_addr = base + 12
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
		addr = self._first_record_addr
		while True:
			try:
				tag = self.read_byte(addr)
			except EofError:
				break # alright, everything lined up nicely!
			r = Record.create(self, addr)
			addr += len(r) # skip to the next record
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

	def name(self, nameid):
		try:
			return self._names[nameid]
		except KeyError:
			raise RefError('name', nameid)

	def _read_bytes(self, start, nbytes):
		if isinstance(start, offset):
			start = start.flatten(self.idsize)
		if isinstance(nbytes, offset):
			nbytes = nbytes.flatten(self.idsize)
		if start < 0:
			raise EofError('tried to read at address %d' % start)
		length = len(self._data)
		if nbytes is not None:
			if nbytes < 0:
				raise ValueError('invalid nbytes', nbytes)
			end = start + nbytes
			if end > length:
				raise EofError('tried to read bytes %d:%d, but file size is %d' % (start, end, length))
		else:
			end = start
			while end < length:
				if self._data[end] == 0:
					break
				end += 1
			else:
				raise EofError('tried to read from %d to null termination, but exceeded file size %d' % (start, length))
		return self._data[start:end]

	def read_bytes(self, addr, nbytes):
		''' Read a byte string of nbytes. '''
		return self._read_bytes(addr, nbytes)

	def read_ascii(self, addr, nbytes=None):
		''' Read an ascii string of nbytes. If nbytes is None, read until a zero byte is found. '''
		return self._read_bytes(addr, nbytes).decode('ascii')

	def read_utf8(self, addr, nbytes):
		''' Read an utf8 string of nbytes. Note: byte count, not character count! '''
		return self._read_bytes(addr, nbytes).decode('utf8')

	def read_jtype(self, addr):
		b, = self._read_bytes(addr, 1)
		try:
			return JavaType(b)
		except ValueError:
			raise FileFormatError('invalid JavaType: 0x%x' % b)

	def read_jvalue(self, addr, jtype):
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
		return rfun(addr)

	def read_char(self, addr):
		return self._read_bytes(addr, 2).decode('utf-16-be')

	def read_byte(self, addr):
		v, = struct.unpack('>B', self._read_bytes(addr, 1))
		return v

	def read_uint(self, addr):
		v, = struct.unpack('>I', self._read_bytes(addr, 4))
		return v

	def read_int(self, addr):
		v, = struct.unpack('>i', self._read_bytes(addr, 4))
		return v

	def read_ushort(self, addr):
		v, = struct.unpack('>H', self._read_bytes(addr, 2))
		return v

	def read_short(self, addr):
		v, = struct.unpack('>h', self._read_bytes(addr, 2))
		return v

	def read_boolean(self, addr):
		b, = self._read_bytes(addr, 1)
		if b == 0:
			return False
		elif b == 1:
			return True
		else:
			raise FileFormatError('invalid boolean value 0x%x' % b)

	def read_id(self, addr):
		bytes = self._read_bytes(addr, self.idsize)
		i = 0
		for b in bytes:
			i = (i << 8) + b
		return i

	def read_float(self, addr):
		v, = struct.unpack('>f', self._read_bytes(addr, 4))
		return v

	def read_double(self, addr):
		v, = struct.unpack('>d', self._read_bytes(addr, 8))
		return v

	def read_long(self, addr):
		v, = struct.unpack('>q', self._read_bytes(addr, 8))
		return v
