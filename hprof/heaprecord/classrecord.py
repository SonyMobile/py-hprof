#!/usr/bin/env python3
#coding=utf8

from .heaprecord import HeapRecord

from ..errors import *
from ..offset import offset, AutoOffsets, idoffset

ioff = AutoOffsets(0,
	'COUNT', 2,
	'DATA')

doff = AutoOffsets(0,
	'NAMEID', idoffset(1),
	'TYPE',   1,
	'END')

class ClassRecord(HeapRecord):
	__slots__ = '_if_start_offset'
	TAG = 0x20

	_offsets = AutoOffsets(1,
		'ID',        idoffset(1),
		'STRACE',    4,
		'SUPER',     idoffset(1),
		'LOADER',    idoffset(1),
		'SIGNER',    idoffset(1),
		'PROT_DOM',  idoffset(1),
		'RESERVED1', idoffset(1),
		'RESERVED1', idoffset(1),
		'OBJSIZE',   4,
		'CPOOLSIZE', 2,
		'CPOOL',     0, # TODO: will need to split offsets here once we allow constant pools
		'NSTATIC',   2,
		'STATICS')

	def __init__(self, hf, addr):
		super().__init__(hf, addr)
		if self._read_ushort(self._off.CPOOLSIZE) != 0:
			raise FileFormatError('cannot handle constant pools yet')
		self._if_start_offset = self._static_fields_end_offset()

	def static_fields(self):
		count = self._read_ushort(self._off.NSTATIC)
		offset = self._off.STATICS
		for i in range(count):
			sfield = StaticFieldRecord(self.hf, self.addr + offset)
			yield sfield
			offset += len(sfield)

	def _static_fields_end_offset(self):
		# pretty much the same as static_fields(), except we just return the offset at the end.
		count = self._read_ushort(self._off.NSTATIC)
		offset = self._off.STATICS
		idsize = self.hf.idsize
		for i in range(count):
			jtype = self._read_jtype(offset + doff[idsize].TYPE)
			offset += doff[idsize].END + jtype.size(idsize)
		return offset

	def instance_fields(self):
		count = self._read_ushort(self._if_start_offset + ioff.COUNT)
		offset = self._if_start_offset + ioff.DATA
		assert type(offset) is int
		for i in range(count):
			ifield = FieldDeclRecord(self.hf, self.addr + offset)
			yield ifield
			offset += len(ifield)

	@property
	def super_class_id(self):
		return self._read_id(self._off.SUPER)

	@property
	def instance_size(self):
		return self._read_uint(self._off.OBJSIZE)

	@property
	def id(self):
		return self._read_id(self._off.ID)

	def __len__(self):
		ifield_count = self._read_ushort(self._if_start_offset + ioff.COUNT)
		return self._if_start_offset + ioff.DATA + ifield_count * doff[self.hf.idsize].END

	def __str__(self):
		return 'ClassRecord(id=0x%x)' % self.id

class FieldDeclRecord(HeapRecord):
	@property
	def type(self):
		return self._read_jtype(doff[self.hf.idsize].TYPE)

	@property
	def nameid(self):
		return self._read_id(doff[self.hf.idsize].NAMEID)

	def __len__(self):
		return doff[self.hf.idsize].END

	def __str__(self):
		return 'FieldDeclRecord(nameid=0x%x, type=%s)' % (self.nameid, self.type)

class StaticFieldRecord(HeapRecord):
	@property
	def decl(self):
		return FieldDeclRecord(self.hf, self.addr)

	@property
	def value(self):
		return self._read_jvalue(doff[self.hf.idsize].END, self.decl.type)

	def __len__(self):
		d = self.decl
		v = len(d) + d.type.size(self.hf.idsize)
		return v

	def __str__(self):
		decl = self.decl
		v = self.value
		if type(v) is int:
			vstr = '0x%x' % v
		else:
			vstr = repr(v)
		return 'StaticFieldRecord(nameid=0x%x, type=%s, value=%s)' % (decl.nameid, decl.type, vstr)
