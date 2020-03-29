# Copyright (C) 2019 Snild Dolkow
# Licensed under the LICENSE.

import re as _re

_namesplit = _re.compile(r'\.|/')

class Heap(dict):
	def __init__(self):
		self.classes = dict() # JavaClassName -> [JavaClass, ...]
		self.classtree = JavaHierarchy()
		self._instances = dict() # JavaClass -> [instance, instance, ...]
		self._deferred_classes = dict()
		self._deferred_primarrays = list()
		self._deferred_objarrays = list()
		self._deferred_objects = list()

	def _classes(self, cls_or_name):
		if isinstance(cls_or_name, JavaClass):
			yield cls_or_name
		else:
			yield from self.classes[cls_or_name]

	def exact_instances(self, cls_or_name):
		''' returns an iterable over all objects of exactly this class. '''
		for cls in self._classes(cls_or_name):
			if cls in self.classes.get('java.lang.Class', ()):
				for lst in self.classes.values():
					yield from lst
			yield from self._instances[cls]

	def all_instances(self, cls_or_name):
		''' returns an iterable over all objects of this class or any of its subclasses. '''
		for cls in self._classes(cls_or_name):
			yield from self.exact_instances(cls)
			for subcls in cls.__subclasses__():
				yield from self.all_instances(subcls)

class JavaHierarchy(object):
	pass

class Ref(object):
	__slots__ = ('_target', '_reftype')

	def __new__(cls, target, reftype):
		# refs to refs aren't allowed
		if type(target) is Ref:
			target = Ref._target.__get__(target)

		# ...and no indirection when we just want the exact type
		if reftype is None or type(target) is reftype:
			return target

		# can't cast to just anything
		if not isinstance(target, reftype):
			raise TypeError('%r is not an instance of %r' % (target, reftype))

		# ...and refs to classes don't make sense.
		if isinstance(target, JavaClass):
			return target

		ref = super().__new__(cls)
		ref._target = target
		ref._reftype = reftype
		return ref

	def __getattribute__(self, name):
		t = Ref._target.__get__(self)
		r = Ref._reftype.__get__(self)
		return t.__getattr__(name, r)

	def __dir__(self):
		t = Ref._target.__get__(self)
		r = Ref._reftype.__get__(self)
		return t.__dir__(r)

	def __repr__(self):
		t = Ref._target.__get__(self)
		r = Ref._reftype.__get__(self)
		objid = JavaObject._hprof_id.__get__(t)
		return '<Ref of type %s to %s 0x%x>' % (r, type(t), objid)

	def __eq__(self, other):
		t = Ref._target.__get__(self)
		return t == other


def cast(obj, desired=None):
	return Ref(obj, desired)


class JavaClassContainer(object):
	__slots__ = ('_name')

	def __init__(self, name):
		self._name = name

	def __str__(self):
		return self._name

	def __hash__(self):
		return hash(self._name)

	def __eq__(self, other):
		return self is other or self._name == str(other)

class JavaPackage(JavaClassContainer):
	''' a Java package, containing JavaClassName objects '''
	def __repr__(self):
		return "<JavaPackage '%s'>" % self


class JavaClassName(JavaClassContainer):
	''' a Java class name that can be used to look up JavaClass objects.
	    May contain nested JavaClassName objects. '''

	def __repr__(self):
		return "<JavaClassName '%s'>" % self


class JavaObject(object):
	__slots__ = (
		'_hprof_id',       # object id
	)

	def __init__(self, objid):
		JavaObject._hprof_id.__set__(self, objid)

	def __repr__(self):
		objid = JavaObject._hprof_id.__get__(self)
		return '<%s 0x%x>' % (type(self), objid)

	def __dir__(self, reftype=None):
		out = set()
		if reftype is None:
			t = type(self)
		else:
			t = reftype
		while t is not JavaObject:
			out.update(t._hprof_ifieldix.keys())
			out.update(t._hprof_sfields.keys())
			bases = t.__bases__
			if len(bases) == 2:
				t = bases[1 - bases.index(JavaArray)]
			else:
				t, = bases
		return tuple(out)

	def __getattr__(self, name, reftype=None):
		if reftype is None:
			t = type(self)
		else:
			t = reftype
		while t is not JavaObject:
			if name in t._hprof_ifieldix:
				ix = t._hprof_ifieldix[name]
				vals = t._hprof_ifieldvals.__get__(self)
				return vals[ix]
			elif name in t._hprof_sfields:
				return t._hprof_sfields[name]
			bases = t.__bases__
			if len(bases) == 2:
				t = bases[1 - bases.index(JavaArray)]
			else:
				t, = bases
		# TODO: implement getattr(x, 'super') to return a Ref?
		# TODO: ...and x.SuperClass too?
		raise AttributeError('type %r has no attribute %r' % (type(self), name))


class JavaArray(JavaObject):
	__slots__ = ()

	def __len__(self):
		try:
			return len(self._hprof_array_data)
		except TypeError:
			self._hprof_array_data = self._hprof_array_data.toarray()
			return len(self._hprof_array_data)

	def __getitem__(self, ix):
		try:
			return self._hprof_array_data[ix]
		except TypeError:
			try:
				self._hprof_array_data = self._hprof_array_data.toarray()
			except AttributeError:
				pass # the TypeError was the caller's fault, not ours
			return self._hprof_array_data[ix]

class JavaClass(type):
	__slots__ = ()

	def __new__(meta, name, supercls, static_attrs, instance_attrs):
		assert '.' not in name
		assert '/' not in name or name.find('/') >= name.find('$$')
		assert '$' not in name or name.find('$') >= name.find('$$')
		assert ';' not in name
		assert isinstance(static_attrs, dict)
		if supercls is None:
			supercls = JavaObject
		if meta is JavaArrayClass and not isinstance(supercls, JavaArrayClass):
			slots = ('_hprof_ifieldvals', '_hprof_array_data')
			supercls = (JavaArray,supercls)
		else:
			slots = ('_hprof_ifieldvals')
			supercls = (supercls,)
		cls = super().__new__(meta, name, supercls, {
			'__slots__': slots,
		})
		cls._hprof_sfields = static_attrs
		cls._hprof_ifields = instance_attrs
		cls._hprof_ifieldix = {name:ix for ix, name in enumerate(instance_attrs)}
		return cls

	def __init__(meta, name, supercls, static_attrs, instance_attrs):
		super().__init__(name, None, None)

	def __str__(self):
		if self.__module__:
			return str(self.__module__) + '.' + self.__name__
		return self.__name__

	def __repr__(self):
		return "<JavaClass '%s'>" % str(self)

	def __instancecheck__(cls, instance):
		if type(instance) is Ref:
			instance = Ref._target.__get__(instance)
		if type(instance) is JavaClass:
			# not pretty...
			if str(cls) in ('java.lang.Object', 'java.lang.Class'):
				return True
		return super().__instancecheck__(instance)

	def __getattr__(self, name):
		t = self
		while t is not JavaObject:
			if name in t._hprof_sfields:
				return t._hprof_sfields[name]
			t, = t.__bases__
		raise AttributeError('type %r has no static attribute %r' % (self, name))


class _DeferredArrayData(object):
	__slots__ = ('bytes', 'jtype')

	def __init__(self, jtype, bytes):
		assert len(bytes) % jtype.size == 0
		self.jtype = jtype
		self.bytes = bytes

	def toarray(self):
		from . import jtype
		if self.jtype is jtype.char:
			import codecs
			# Decode bytes pair-by-pair.
			# Not pretty, but we want the same behavior as Java, which
			# means each char element is exactly 16 bits; surrogate pairs
			# therefore must span two array indices.
			return ''.join(
				codecs.decode(self.bytes[i:i+2], 'utf-16-be', 'surrogatepass')
				for i in range(0, len(self.bytes), 2)
			)
		else:
			import struct
			count = len(self.bytes) // self.jtype.size
			fmt = '>%d%s' % (count, self.jtype.packfmt)
			return struct.unpack(fmt, self.bytes)

class JavaArrayClass(JavaClass):
	__slots__ = ()


def _get_or_create_container(container, parts, ctype):
	for p in parts:
		assert p
		assert '.' not in p
		assert ';' not in p
		assert '/' not in p or p.find('/') >= p.find('$$')
		assert '$' not in p or p.find('$') >= p.find('$$')
		if hasattr(container, p):
			container = getattr(container, p)
			assert isinstance(container, ctype), container
		else:
			if isinstance(container, JavaClassContainer):
				next = ctype(str(container) + '.' + p)
			else:
				next = ctype(p)
			setattr(container, p, next)
			container = next
	return container


_typechar_to_name = {
	'Z': 'boolean',
	'C': 'char',
	'F': 'float',
	'D': 'double',
	'B': 'byte',
	'S': 'short',
	'I': 'int',
	'J': 'long',
}

_name_to_typechar = {
	'boolean': 'Z',
	'char': 'C',
	'float': 'F',
	'double': 'D',
	'byte': 'B',
	'short': 'S',
	'int': 'I',
	'long': 'J',
}


def _create_class(container, name, supercls, staticattrs, instanceattrs):
	# android hprofs may have slightly different class name format...
	if '.' in name:
		name = name.replace('.', '/')
	if name.endswith('[]'):
		a = 0
		while name.endswith('[]'):
			name = name[:-2]
			a += 1
		if name in _name_to_typechar:
			name = _name_to_typechar[name]
		else:
			name = 'L' + name + ';'
		name = a * '[' + name

	# okay, now we should be "normalized"
	nests = 0
	while name[nests] == '[':
		nests += 1

	if nests:
		if name[nests] == 'L':
			assert name.endswith(';'), name
			name = name[nests+1:-1]
		else:
			assert len(name) == nests + 1, name
			name = name[nests]
			name = _typechar_to_name[name]

	assert '.' not in name, name
	assert ';' not in name, name
	assert '[' not in name, name

	# special handling for lambda names (jvm-specific name generation?)
	# in short: everything after $$ is part of the class name.
	dollars = name.find('$$')
	if dollars >= 0:
		extra = name[dollars:]
		name  = name[:dollars]
	else:
		extra = ''

	name = name.split('/')
	container = _get_or_create_container(container, name[:-1], JavaPackage)
	name = name[-1].split('$')
	if extra:
		name[-1] += extra
	name[-1] += nests * '[]'
	container = _get_or_create_container(container, name[:-1], JavaClassName)
	classname = _get_or_create_container(container, name[-1:], JavaClassName)
	name = name[-1]
	if nests:
		cls = JavaArrayClass(name, supercls, staticattrs, instanceattrs)
	else:
		cls = JavaClass(name, supercls, staticattrs, instanceattrs)
	if isinstance(container, JavaClassContainer):
		type.__setattr__(cls, '__module__', container)
	else:
		type.__setattr__(cls, '__module__', None)
	return classname, cls
