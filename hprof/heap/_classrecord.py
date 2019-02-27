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

class Class(Allocation):
	'''A Class object in a dump.

	Class objects contain static attribute values, as well as offsets for instance fields.

	Members:
	hprof_file -- the HprofFile this object belongs to.
	hprof_addr -- the byte address of this object in hprof_file.
	hprof_heap -- the hprof.Heap this object belongs to.
	'''

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
		'''yield all the static fields of this class and its super classes.'''
		count = self._hprof_ushort(self._hprof_sf_start_offset)
		offset = self._hprof_sf_start_offset + 2
		for i in range(count):
			sfield = StaticField(self.hprof_file, self.hprof_addr + offset)
			yield sfield
			offset += sfield._hprof_len
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
		'''yield all instance field declarations'''
		count = self._hprof_ushort(self._hprof_if_start_offset + ioff.COUNT)
		offset = self._hprof_if_start_offset + ioff.DATA
		assert type(offset) is int
		for i in range(count):
			ifield = FieldDecl(self.hprof_file, self.hprof_addr + offset)
			yield ifield
			offset += ifield._hprof_len

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
		'''return the ID of the super class object (or zero, if this is java.lang.Object)'''
		return self._hprof_id(self._hproff.SUPER)

	@property
	def hprof_super_class(self):
		'''return the super class object of this class (or None, if this is java.lang.Object)'''
		return self.hprof_heap.dump.get_class(self.hprof_super_class_id)

	def hprof_subclasses(self):
		'''yield all direct subclasses of this class.'''
		yield from self.hprof_heap.dump._subclasses(self)

	@property
	def hprof_class_id(self):
		'''return the ID of this object's class.

		Since this object is a class, the returned value will be the ID of java.lang.Class.
		'''
		return self.hprof_file.get_class_info('java.lang.Class').class_id

	@property
	def hprof_instance_size(self):
		'''return the size of instances of this class, as declared by the class record.

		This value may or may not be accurate, and the exact definition may vary with virtual
		machine (or even hprof dumper) implementations.

		Array classes can not take the array instance's length into consideration. This limitation
		is shared by all implementations, since the class record just contains a simple integer.
		'''
		return self._hprof_uint(self._hproff.OBJSIZE)

	@property
	def hprof_name(self):
		'''return the name of this class.'''
		return self.hprof_file.get_class_info(self.hprof_id).class_name

	@property
	def _hprof_len(self):
		ifield_count = self._hprof_ushort(self._hprof_if_start_offset + ioff.COUNT)
		return self._hprof_if_start_offset + ioff.DATA + ifield_count * doff[self.hprof_file.idsize].END

	def __str__(self):
		return 'Class(%s)' % self.hprof_name

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

class FieldDecl(HprofSlice):
	'''A field declaration, containing a name and type.

	Members:
	hprof_file -- the HprofFile this field belongs to.
	hprof_addr -- the byte address of this field in hprof_file.
	'''
	@property
	def type(self):
		'''the type of this field, as an hprof.JavaType value.

		hprof files do not contain the declared types of fields, so all reference-typed fields will
		have a JavaType.object here.'''
		return self._hprof_jtype(doff[self.hprof_file.idsize].TYPE)

	@property
	def name(self):
		'''the name of this field.'''
		nameid = self._hprof_id(doff[self.hprof_file.idsize].NAMEID)
		return self.hprof_file.name(nameid).str

	@property
	def _hprof_len(self):
		return doff[self.hprof_file.idsize].END

	def __str__(self):
		return 'FieldDecl(name=%s, type=%s)' % (self.name, self.type)

class StaticField(HprofSlice):
	'''A static field.

	Members:
	hprof_file -- the HprofFile this field belongs to.
	hprof_addr -- the byte address of this field in hprof_file.
	'''
	@property
	def decl(self):
		'''the declaration of this field.'''
		return FieldDecl(self.hprof_file, self.hprof_addr)

	@property
	def value(self):
		'''the value of this field.'''
		return self._hprof_jvalue(doff[self.hprof_file.idsize].END, self.decl.type)

	@property
	def _hprof_len(self):
		d = self.decl
		v = d._hprof_len + d.type.size(self.hprof_file.idsize)
		return v

	def __str__(self):
		decl = self.decl
		v = self.value
		if type(v) is int:
			vstr = '0x%x' % v
		else:
			vstr = repr(v)
		return 'StaticField(name=%s, type=%s, value=%s)' % (decl.name, decl.type, vstr)
