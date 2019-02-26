from ._heaprecord import HeapRecord

from .._offset import offset, AutoOffsets, idoffset
from .._errors import RefError

class GcRoot(HeapRecord):
	'''Common operations for information about garbage collection roots.

	Members:
	hprof_file -- the HprofFile this root belongs to.
	hprof_addr -- the byte address of this root record in hprof_file.
	'''

	@property
	def objid(self):
		'''the object ID that's directly being kept alive by this gc root.'''
		return self._hprof_id(self._hproff.ID)

	@property
	def _hprof_len(self):
		return self._hproff.END

	def _info(self):
		return 'objid=0x%x' % self.objid

	def __str__(self):
		return '%s(%s)' % (type(self).__name__, self._info())

class UnknownRoot(GcRoot):
	'''A garbage collection root that does not fit into any of the other types.

	Members:
	hprof_file -- the HprofFile this root belongs to.
	hprof_addr -- the byte address of this root record in hprof_file.
	'''

	HPROF_DUMP_TAG = 0xff
	_hprof_offsets = AutoOffsets(1, 'ID', idoffset(1), 'END')

class GlobalJniRoot(GcRoot):
	'''A garbage collection root created through the NewGlobalRef() JNI function.

	Members:
	hprof_file -- the HprofFile this root belongs to.
	hprof_addr -- the byte address of this root record in hprof_file.
	'''

	HPROF_DUMP_TAG = 0x01
	_hprof_offsets = AutoOffsets(1,
			'ID',     idoffset(1),
			'REFID',  idoffset(1),
			'END')

	@property
	def grefid(self):
		'''the ID of the reference (NOT the referenced object)'''
		return self._hprof_id(self._hproff.REFID)

	def _info(self):
		return super()._info() + ', grefid=0x%x' % self.grefid

class LocalJniRoot(GcRoot):
	'''A garbage collection root created through the NewLocalRef() JNI function.

	Members:
	hprof_file -- the HprofFile this root belongs to.
	hprof_addr -- the byte address of this root record in hprof_file.
	'''

	HPROF_DUMP_TAG = 0x02
	_hprof_offsets = AutoOffsets(1,
			'ID',     idoffset(1),
			'STRACE', 4,
			'FRAME',  4,
			'END')

	def _info(self):
		return super()._info() + ' in <func>' # TODO: actually show the function here.

class JavaStackRoot(GcRoot):
	'''A garbage collection root caused by a reference on the Java stack.

	Members:
	hprof_file -- the HprofFile this root belongs to.
	hprof_addr -- the byte address of this root record in hprof_file.
	'''

	HPROF_DUMP_TAG = 0x03
	_hprof_offsets = AutoOffsets(1,
			'ID',     idoffset(1),
			'THREAD', 4,
			'FRAME',  4,
			'END')

	def _info(self):
		return super()._info() + ' in <func>' # TODO: not <func>

class NativeStackRoot(GcRoot):
	'''A garbage collection root caused by ...something native. Maybe the java/jni transition?

	Members:
	hprof_file -- the HprofFile this root belongs to.
	hprof_addr -- the byte address of this root record in hprof_file.
	'''

	HPROF_DUMP_TAG = 0x04
	_hprof_offsets = AutoOffsets(1,
			'ID',     idoffset(1),
			'THREAD', 4,
			'END')

	def _info(self):
		return super()._info() + ' from thread ???' # TODO: not "???"

class StickyClassRoot(GcRoot):
	'''A garbage collection root for classes required by the runtime.

	Members:
	hprof_file -- the HprofFile this root belongs to.
	hprof_addr -- the byte address of this root record in hprof_file.
	'''

	HPROF_DUMP_TAG = 0x05
	_hprof_offsets = AutoOffsets(1, 'ID', idoffset(1), 'END')

class ThreadBlockRoot(GcRoot):
	'''A garbage collection root caused by a reference from a thread block (whatever that is).

	Members:
	hprof_file -- the HprofFile this root belongs to.
	hprof_addr -- the byte address of this root record in hprof_file.
	'''

	HPROF_DUMP_TAG = 0x06
	_hprof_offsets = AutoOffsets(1, 'ID', idoffset(1), 'THREAD', 4, 'END')

class MonitorRoot(GcRoot):
	'''A garbage collection root caused by the object currently being used as a monitor.

	Members:
	hprof_file -- the HprofFile this root belongs to.
	hprof_addr -- the byte address of this root record in hprof_file.
	'''

	HPROF_DUMP_TAG = 0x07
	_hprof_offsets = AutoOffsets(1, 'ID', idoffset(1), 'END')

class ThreadRoot(GcRoot):
	'''A garbage collection root caused by the referenced object being a thread.

	Members:
	hprof_file -- the HprofFile this root belongs to.
	hprof_addr -- the byte address of this root record in hprof_file.
	'''

	HPROF_DUMP_TAG = 0x08
	_hprof_offsets = AutoOffsets(1,
			'ID',     idoffset(1),
			'THREAD', 4,
			'STRACE', 4,
			'END')

	def _info(self):
		return super()._info() + ' from thread ???' # TODO: actually show the thread here.

class InternedStringRoot(GcRoot):
	'''A garbage collection root caused by a string being interned (Android ART-specific).

	Members:
	hprof_file -- the HprofFile this root belongs to.
	hprof_addr -- the byte address of this root record in hprof_file.
	'''

	HPROF_DUMP_TAG = 0x89
	_hprof_offsets = AutoOffsets(1, 'ID', idoffset(1), 'END')

class VmInternalRoot(GcRoot):
	'''A garbage collection root for... super-secret vm internal reasons (Android ART-specific).

	Members:
	hprof_file -- the HprofFile this root belongs to.
	hprof_addr -- the byte address of this root record in hprof_file.
	'''

	HPROF_DUMP_TAG = 0x8d
	_hprof_offsets = AutoOffsets(1,
			'ID',    idoffset(1),
			'END')
