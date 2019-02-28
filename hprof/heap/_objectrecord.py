from ._heaprecord import Allocation

from .._errors import FieldNotFoundError, UnfamiliarStringError, Error
from .._offset import offset, AutoOffsets, idoffset
from .._types import JavaType


class Object(Allocation):
	'''A normal object instance on the heap (i.e. not a Class or an array).

	Members:
	hprof_file -- the HprofFile this object belongs to.
	hprof_addr -- the byte address of this object in hprof_file.
	hprof_heap -- the hprof.Heap this object belongs to.
	'''

	HPROF_DUMP_TAG = 0x21

	_hprof_offsets = AutoOffsets(1,
		'ID',       idoffset(1),
		'STRACE',   4,
		'CLSID',    idoffset(1),
		'DATASIZE', 4,
		'DATA'
	)

	@property
	def hprof_class_id(self):
		'''the ID of this object's class.'''
		return self._hprof_id(self._hproff.CLSID)

	@property
	def _hprof_len(self):
		return self._hproff.DATA + self._hprof_uint(self._hproff.DATASIZE)

	def _hprof_strval(self):
		try:
			data = self.value
		except FieldNotFoundError:
			raise UnfamiliarStringError('java.lang.String has an unfamiliar internal structure')
		if data is None:
			return '' # assume that a null value means 'empty string'
		try:
			dcls = self.hprof_file.get_class_info(data.hprof_class_id)
			dcname = dcls.class_name
			if dcname == 'char[]':
				return data.hprof_decode()
			elif dcname == 'byte[]':
				return bytes.decode(bytes(data), 'utf-8')
			raise Exception('String.value found, but was not a type we can handle')
		except Exception:
			raise UnfamiliarStringError('failed to decode value of java.lang.String object')

	def __eq__(self, other):
		sup = super().__eq__(other)
		if sup:
			return True
		cid = self.hprof_class_id
		cname = self.hprof_file.get_class_info(cid).class_name
		if cname != 'java.lang.String':
			return False
		if type(other) is Object and other.hprof_class_id == cid:
			return self._hprof_strval() == other._hprof_strval()
		else:
			return type(other) is str and self._hprof_strval() == other

	def __str__(self):
		cid = self.hprof_class_id
		cname = self.hprof_file.get_class_info(cid).class_name
		if cname == 'java.lang.String':
			try:
				return self._hprof_strval()
			except Exception:
				pass
		cname = cname.rsplit('.', 1)[-1]
		return '%s(id=0x%x)' % (cname, self.hprof_id)

	def __repr__(self):
		sid = self.hprof_id
		cid = self.hprof_class_id
		cname = self.hprof_file.get_class_info(cid).class_name
		if cname == 'java.lang.String':
			try:
				strval = self._hprof_strval()
				return 'Object(class=%s, id=0x%x, value=%r)' % (cname, sid, strval)
			except Exception as e:
				pass
		return 'Object(class=%s, id=0x%x)' % (cname, sid)
