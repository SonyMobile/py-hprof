#!/usr/bin/env python3
#coding=utf8

from .heaprecord import HeapRecord

from ..errors import *
from ..offset import offset, AutoOffsets, idoffset

def _only_last(generator):
	for prev in generator:
		pass
	return prev

def _except_last(generator):
	prev = next(generator)
	for val in generator:
		yield prev
		prev = val

coff = AutoOffsets(1,
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

ioff = AutoOffsets(0,
	'COUNT', 2,
	'DATA')

doff = AutoOffsets(0,
	'NAMEID', idoffset(1),
	'TYPE',   1,
	'END')

class ClassRecord(HeapRecord):
	TAG = 0x20

	def __init__(self, hf, addr):
		super().__init__(hf, addr)
		if self._read_ushort(coff.CPOOLSIZE) != 0:
			raise FileFormatError('cannot handle constant pools yet')

	def _read_static_fields(self):
		count = self._read_ushort(coff.NSTATIC)
		offset = coff.STATICS.flatten(self.hf.idsize)
		for i in range(count):
			sfield = StaticFieldRecord(self.hf, self.addr + offset)
			yield sfield
			offset += len(sfield)
		yield offset

	def _if_start_offset(self):
		for v in self._read_static_fields():
			pass
		return v

	def _read_instance_fields(self):
		base = self._if_start_offset()
		count = self._read_ushort(base + ioff.COUNT)
		offset = base + ioff.DATA
		assert type(offset) is int
		for i in range(count):
			ifield = FieldDeclRecord(self.hf, self.addr + offset)
			yield ifield
			offset += len(ifield)
		yield offset

	def instance_fields(self):
		yield from _except_last(self._read_instance_fields())

	def static_fields(self):
		yield from _except_last(self._read_static_fields())

	@property
	def super_class_id(self):
		return self._read_id(coff.SUPER)

	@property
	def instance_size(self):
		return self._read_uint(coff.OBJSIZE)

	@property
	def id(self):
		return self._read_id(coff.ID)

	def __len__(self):
		return _only_last(self._read_instance_fields())

	def __str__(self):
		return 'ClassRecord(id=0x%x)' % self.id

class FieldDeclRecord(HeapRecord):
	@property
	def type(self):
		return self._read_jtype(doff.TYPE)

	@property
	def nameid(self):
		return self._read_id(doff.NAMEID)

	def __len__(self):
		return doff.END.flatten(self.hf.idsize)

	def __str__(self):
		return 'FieldDeclRecord(nameid=0x%x, type=%s)' % (self.nameid, self.type)

class StaticFieldRecord(HeapRecord):
	@property
	def decl(self):
		return FieldDeclRecord(self.hf, self.addr)

	@property
	def value(self):
		return self._read_jvalue(doff.END, self.decl.type)

	def __len__(self):
		d = self.decl
		v = len(d) + d.type.size()
		if type(v) is not int:
			v = v.flatten(self.hf.idsize)
		return v

	def __str__(self):
		decl = self.decl
		v = self.value
		if type(v) is int:
			vstr = '0x%x' % v
		else:
			vstr = repr(v)
		return 'StaticFieldRecord(nameid=0x%x, type=%s, value=%s)' % (decl.nameid, decl.type, vstr)
