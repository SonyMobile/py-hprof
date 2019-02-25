#!/usr/bin/env python3
#coding=utf8

from ._heaprecord import Allocation

from .._errors import *
from .._offset import offset, AutoOffsets, idoffset
from .._commonrecord import HprofSlice
from .._types import JavaType

ioff = AutoOffsets(0,
	'COUNT', 2,
	'DATA')

doff = AutoOffsets(0,
	'NAMEID', idoffset(1),
	'TYPE',   1,
	'END')

class ClassRecord(Allocation):
	__slots__ = '_hprof_sf_start_offset', '_hprof_if_start_offset'
	HPROF_DUMP_TAG = 0x20

	_hprof_offsets = AutoOffsets(1,
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
		'CPOOL')

	def __init__(self, hf, addr):
		super().__init__(hf, addr)
		self._hprof_sf_start_offset = self._hprof_cpool_end_offset()
		self._hprof_if_start_offset = self._hprof_static_fields_end_offset()

	def _hprof_cpool_end_offset(self):
		count = self._hprof_ushort(self._hproff.CPOOLSIZE)
		offset = self._hproff.CPOOL
		idsize = self.hprof_file.idsize
		for i in range(count):
			jtype = self._hprof_jtype(offset+2)
			offset += 3 + jtype.size(idsize)
		return offset

	def hprof_static_fields(self):
		count = self._hprof_ushort(self._hprof_sf_start_offset)
		offset = self._hprof_sf_start_offset + 2
		for i in range(count):
			sfield = StaticFieldRecord(self.hprof_file, self.hprof_addr + offset)
			yield sfield
			offset += len(sfield)
		superid = self.hprof_super_class_id
		if superid != 0:
			supercls = self.hprof_heap.dump.get_class(superid)
			yield from supercls.hprof_static_fields()

	def _hprof_static_fields_end_offset(self):
		# pretty much the same as static_fields(), except we just return the offset at the end.
		count = self._hprof_ushort(self._hprof_sf_start_offset)
		offset = self._hprof_sf_start_offset + 2
		idsize = self.hprof_file.idsize
		typeoff = doff[idsize].TYPE
		decllen = doff[idsize].END
		for i in range(count):
			jtype = self._hprof_jtype(offset + typeoff)
			offset += decllen + jtype.size(idsize)
		return offset

	def hprof_instance_fields(self):
		count = self._hprof_ushort(self._hprof_if_start_offset + ioff.COUNT)
		offset = self._hprof_if_start_offset + ioff.DATA
		assert type(offset) is int
		for i in range(count):
			ifield = FieldDeclRecord(self.hprof_file, self.hprof_addr + offset)
			yield ifield
			offset += len(ifield)

	def _hprof_instance_field_lookup(self, name):
		count = self._hprof_ushort(self._hprof_if_start_offset + ioff.COUNT)
		offset = self._hprof_if_start_offset + ioff.DATA
		field_offset = 0
		idsize = self.hprof_file.idsize
		typeoff = doff[idsize].TYPE
		decllen = doff[idsize].END
		for i in range(count):
			# TODO: could we do lookups by name id, rather than (string) name? Probably. Need to look out for duplicate names with different IDs, though.
			field_name_id = self._hprof_id(offset)
			field_type = self._hprof_jtype(offset + typeoff)
			if self.hprof_file.name(field_name_id).str == name:
				return field_type, field_offset
			offset += decllen
			field_offset += field_type.size(idsize)
		super_id = self.hprof_super_class_id
		if super_id == 0:
			raise FieldNotFoundError('instance', name, self.hprof_name)
		supercls = self.hprof_heap.dump.get_class(super_id)
		try:
			field_type, superoffset = supercls._hprof_instance_field_lookup(name)
		except FieldNotFoundError as e:
			e.add_class(self.hprof_name)
			raise e
		return field_type, field_offset + superoffset

	@property
	def hprof_super_class_id(self):
		return self._hprof_id(self._hproff.SUPER)

	@property
	def hprof_instance_size(self):
		return self._hprof_uint(self._hproff.OBJSIZE)

	@property
	def hprof_name(self):
		return self.hprof_file.get_class_info(self.hprof_id).class_name

	def __len__(self):
		ifield_count = self._hprof_ushort(self._hprof_if_start_offset + ioff.COUNT)
		return self._hprof_if_start_offset + ioff.DATA + ifield_count * doff[self.hprof_file.idsize].END

	def __str__(self):
		return 'ClassRecord(id=0x%x)' % self.hprof_id

	def __getattr__(self, name):
		return self[name]

	def __getitem__(self, name):
		for sf in self.hprof_static_fields():
			decl = sf.decl
			if decl.name == name:
				t = decl.type
				v = sf.value
				if t == JavaType.object:
					return self.hprof_heap.dump.get_object(v)
				else:
					return v
		super_id = self.hprof_super_class_id
		if super_id == 0:
			raise FieldNotFoundError('static', name, self.hprof_name)
		supercls = self.hprof_heap.dump.get_class(super_id)
		try:
			return supercls[name]
		except FieldNotFoundError as e:
			e.add_class(self.hprof_name)
			raise

class FieldDeclRecord(HprofSlice):
	@property
	def type(self):
		return self._hprof_jtype(doff[self.hprof_file.idsize].TYPE)

	@property
	def name(self):
		nameid = self._hprof_id(doff[self.hprof_file.idsize].NAMEID)
		return self.hprof_file.name(nameid).str

	def __len__(self):
		return doff[self.hprof_file.idsize].END

	def __str__(self):
		return 'FieldDeclRecord(name=%s, type=%s)' % (self.name, self.type)

class StaticFieldRecord(HprofSlice):
	@property
	def decl(self):
		return FieldDeclRecord(self.hprof_file, self.hprof_addr)

	@property
	def value(self):
		return self._hprof_jvalue(doff[self.hprof_file.idsize].END, self.decl.type)

	def __len__(self):
		d = self.decl
		v = len(d) + d.type.size(self.hprof_file.idsize)
		return v

	def __str__(self):
		decl = self.decl
		v = self.value
		if type(v) is int:
			vstr = '0x%x' % v
		else:
			vstr = repr(v)
		return 'StaticFieldRecord(name=%s, type=%s, value=%s)' % (decl.name, decl.type, vstr)
