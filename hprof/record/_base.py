from datetime import timedelta

from .._offset import *
from .._commonrecord import HprofSlice

def _word_groups(b):
	for i in range(0, len(b), 4):
		yield b[i:i+4]

def _hex_groups(b):
	for g in _word_groups(b):
		yield ''.join('%02x' % b for b in g)


offsets = AutoOffsets(0,
	'TAG',     1,
	'TIME',    4,
	'BODYLEN', 4,
	'BODY'
)

def create(hf, addr):
	'''create an instance of an appropriate Record subclass, based on the tag found at addr.

	You'll probably be better off getting them from HprofFile.records().'''
	tag = hf.read_byte(addr)
	# TODO: some form of caching here might not be a bad idea.
	rtype = Unhandled
	for candidate in Record.__subclasses__():
		if getattr(candidate, 'TAG', None) == tag:
			rtype = candidate
	return rtype(hf, addr)

class Record(HprofSlice):
	'''Base record type, extended by all other top-level record types.

	Members:
	hprof_file -- the HprofFile this record belongs to.
	hprof_addr -- the byte address of this record in hprof_file.
	'''
	@property
	def rawbody(self):
		'''the raw body bytes of this record; probably not interesting in most cases'''
		return self.hprof_file.read_bytes(self.hprof_addr+9, self._hprof_len - 9)

	@property
	def timestamp(self):
		'''the absolute timestamp of this record.'''
		return self.hprof_file.starttime + self.relative_timestamp

	@property
	def relative_timestamp(self):
		'''the timestamp of this record, relative to the start time of the hprof file.'''
		return timedelta(microseconds = self.hprof_file.read_uint(self.hprof_addr + 1))

	@property
	def _hprof_len(self):
		return 9 + self.hprof_file.read_uint(self.hprof_addr + 5)

	def __str__(self):
		data = self.rawbody
		if len(data) > 40:
			hexdata = ' '.join(_hex_groups(self.rawbody[:32])) + ' ...'
		else:
			hexdata = ' '.join(_hex_groups(self.rawbody))
		if hexdata:
			hexdata = ' ' + hexdata + ' '
		return '%s(%s)' % (type(self).__name__, hexdata)


class Unhandled(Record):
	'''A record of a type that this library does not recognize.

	Thanks to the record format explicitly declaring the length of each record, it is not
	necessarily a showstopper -- we may be able to ignore it without problems.

	If you want to handle it yourself, the rawbody property may be useful. But hey, if you're doing
	that, maybe you should be contributing to the library instead?

	Members:
	hprof_file -- the HprofFile this record belongs to.
	hprof_addr -- the byte address of this record in hprof_file.
	'''
