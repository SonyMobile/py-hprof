#!/usr/bin/env python3
#coding=utf8

from datetime import datetime
from mmap import mmap, MAP_PRIVATE, PROT_READ

import builtins
import struct

from .heapdump import Dump
from ._errors import *
from ._offset import offset
from .record import create, HeapDumpSegment, HeapDumpEnd, Utf8, ClassLoad
from ._types import JavaType

_jtlookup = {}
for _jt in JavaType:
	_jtlookup[_jt.value] = _jt

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
		accepted_versions = ('1.0.2', '1.0.3')
		if version not in accepted_versions:
			raise FileFormatError('bad version %s; expected one of %s' % (version, ', '.join(accepted_versions)))
		base = 13 + len(version) + 1

		self.idsize = self.read_uint(base)
		timestamp_ms = (self.read_uint(base + 4) << 32) + self.read_uint(base + 8)
		self.starttime = datetime.fromtimestamp(timestamp_ms / 1000)
		self._first_record_addr = base + 12
		self._dumps = None
		self._names = None
		self._names_done = False

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

	def _gen_from_records(self, need_dumps):
		''' traversing all the records can take a while; try to generate several things at once '''
		need_names = not self._names_done
		seen_name_ids = set()
		if self._names is None:
			self._names = {}
		names = self._names
		curdump = None
		dumps = []
		for r in self.records():
			if need_names and type(r) is Utf8:
				nameid = r.id
				if nameid in names:
					# might be okay; we may be recursing (through Dump/Heap classes)
					if nameid in seen_name_ids:
						old = names[nameid]
						raise FileFormatError(
								'duplicate name id 0x%x: "%s" at 0x%x and "%s" at 0x%x'
								% (nameid, old.str, old.hprof_addr, r.str, r.hprof_addr))
				else:
					names[nameid] = r
				seen_name_ids.add(nameid)
			if need_dumps and type(r) is HeapDumpSegment:
				if curdump is None:
					curdump = Dump(self)
					dumps.append(curdump)
				curdump._add_segment(r)
			elif need_dumps and type(r) is HeapDumpEnd:
				if curdump is None:
					dumps.append(Dump(self))
				curdump = None
		if need_names:
			self._names_done = True
		if need_dumps:
			self._dumps = tuple(dumps)

	def records(self):
		addr = self._first_record_addr
		while True:
			try:
				tag = self.read_byte(addr)
			except EofError:
				break # alright, everything lined up nicely!
			r = create(self, addr)
			addr += len(r) # skip to the next record
			yield r

	def dumps(self):
		if self._dumps is None:
			self._gen_from_records(True)
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
		except (KeyError, TypeError):
			pass
		if not self._names_done:
			self._gen_from_records(False)
		try:
			return self._names[nameid]
		except KeyError:
			raise RefError('name', nameid)

	def get_class_info(self, clsid):
		# TODO: probably cache this.
		for r in self.records():
			if type(r) is ClassLoad and r.class_id == clsid:
				return r
		raise ClassNotFoundError('ClassLoad record for class id 0x%x' % clsid)

	def get_primitive_array_class_info(self, primitive_type):
		# TODO: probably cache this.
		expected_name = primitive_type.name + '[]'
		for r in self.records():
			if type(r) is ClassLoad and r.class_name == expected_name:
				return r
		raise ClassNotFoundError('Primitive array type %s[]' % primitive_type)

	def _read_bytes(self, start, nbytes):
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
			return _jtlookup[b]
		except KeyError as e:
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
