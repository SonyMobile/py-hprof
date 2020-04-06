# Copyright (C) 2019 Snild Dolkow
# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

'''
Classes and functions implementing a Java-like object model.
'''

import re as _re

_NAMESPLIT = _re.compile(r'\.|/')

class Heap(dict):
	''' A heap dump from an hprof file. An hprof file can technically contain
	several of these, but they usually don't.

	>>> heap, = hf.heaps
	>>> print(len(heap), 'objects')
	24465 objects

	If you happen to know the id of an object, you can get at it very quickly:

	>>> print(heap[0xce7e8000].make)
	Fånark

	Otherwise, you can find instances by class:

	>>> bikes = list(heap.exact_instances('com.example.cars.Bike'))
	>>> mine = bikes[0]
	>>> print(mine)
	Bike@ce7e8000
	>>> print(mine.make)
	Fånark
	>>> print(mine.make.value) # the String's backing byte array
	byte[6] {70, -27, 110, 97, 114, 107}

	Note that a Java heap may contain multiple classes with the same name -- one
	is allowed in each class loader. Therefore, `heap.classes` map class names
	to a list of classes:

	>>> heap.classes[heap.classtree.com.example.cars.Bike]
	[<JavaClass 'com.example.cars.Bike'>]

	Members:
	classes -- a dict mapping java class names to class instance lists.
	classtree -- a JavaHierarchy object, allowing tab completion of class names
	'''

	def __init__(self):
		super().__init__()
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
		''' returns an iterable over all objects of exactly this class.

		The argument may be a class instance:

		>>> car_cls, = heap.classes['com.example.cars.Car']
		>>> list(heap.exact_instances(car_cls))
		[<com.example.cars.Car 0x...>, <com.example.cars.Car 0x...>]

		...or a fully qualified class name:

		>>> list(heap.exact_instances('com.example.cars.Car'))
		[<com.example.cars.Car 0x...>, <com.example.cars.Car 0x...>]
		'''
		for cls in self._classes(cls_or_name):
			if cls in self.classes.get('java.lang.Class', ()):
				for lst in self.classes.values():
					yield from lst
			yield from self._instances[cls]

	def all_instances(self, cls_or_name):
		''' returns an iterable over all objects of this class or any of its subclasses.

		The argument may be a class instance:

		>>> car_cls, = heap.classes['com.example.cars.Car']
		>>> list(heap.all_instances(car_cls))
		[<com.example.cars.Car 0x...>, <com.example.cars.Car 0x...>, <com.example.cars.Limo 0x...>]

		...or a fully qualified class name:

		>>> list(heap.all_instances('com.example.cars.Car'))
		[<com.example.cars.Car 0x...>, <com.example.cars.Car 0x...>, <com.example.cars.Limo 0x...>]
		'''
		for cls in self._classes(cls_or_name):
			yield from self.exact_instances(cls)
			for subcls in cls.__subclasses__():
				yield from self.all_instances(subcls)

class JavaHierarchy(object):
	''' Accessible as Heap.classtree. Allows tab completion of class names.

	>>> heap.classtree.com.example.cars.Bike
	<JavaClassName 'com.example.cars.Bike'>
	'''
	pass

class Ref(object):
	''' A reference to an object, where the reference type is different from the
	object type.

	>>> supercls, = heap.classes['com.example.ShadowI']
	>>> subcls,   = heap.classes['com.example.ShadowII']
	>>> issubclass(subcls, supercls)
	True

	ShadowI declares a field 'val', initialized to 4. ShadowII shadows 'val'
	with its own declaration, initializing it to 5.

	>>> a, = heap.exact_instances(supercls)
	>>> b, = heap.exact_instances(subcls)
	>>> a.val
	4
	>>> b.val
	5

	By casting b to its superclass, we can access the shadowed field.

	>>> b = cast(b, supercls)
	>>> b
	<Ref of type com.example.ShadowI to com.example.ShadowII 0x...>
	>>> b.val
	4

	'''
	__slots__ = ('_target', '_reftype')

	def __new__(cls, target, reftype):
		# refs to refs aren't allowed
		if type(target) is Ref: # pylint: disable=unidiomatic-typecheck
			target = Ref._target.__get__(target)

		# ...and no indirection when we just want the exact type
		if reftype is None or type(target) is reftype: # pylint: disable=unidiomatic-typecheck
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
	''' A perhaps more reader-friendly way of saying Ref(obj, desired). '''
	return Ref(obj, desired)


class JavaClassContainer(object):
	''' Common ancestor of JavaPackage and JavaClassName. '''

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
	''' a Java package, containing JavaPackage and JavaClassName objects '''
	def __repr__(self):
		return "<JavaPackage '%s'>" % self


class JavaClassName(JavaClassContainer):
	''' a Java class name that can be used to look up JavaClass objects.
	    May contain nested JavaClassName objects.

	    These can be used anywhere class names are accepted.
	    '''

	def __repr__(self):
		return "<JavaClassName '%s'>" % self


class JavaObject(object):
	''' Base class for all Java objects that are not classes. '''

	__slots__ = (
		'_hprof_id',       # object id
	)

	def __init__(self, objid):
		JavaObject._hprof_id.__set__(self, objid)

	def __str__(self):
		objid = JavaObject._hprof_id.__get__(self)
		simple_name = type(self).__name__
		outer = type(self).__module__
		while isinstance(outer, JavaClassName):
			outername = str(outer).rsplit('.', 1)[-1]
			simple_name = '%s.%s' % (outername, simple_name)
			outer = outer.__module__
		return '%s@%x' % (simple_name, objid)

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
	''' Base class for all Java arrays. '''

	# _hprof_array_data is not in the slots here because it creates layout
	# conflicts with multiple bases; it will exist, I promise.
	# pylint: disable=assigning-non-slot
	__slots__ = ()

	def __init__(self, objid, array_data):
		super().__init__(objid)
		self._hprof_array_data = array_data

	def __len__(self):
		try:
			# TODO: may be a good idea to make len() work on deferred array data
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

	def __str__(self):
		typename = super().__str__().rsplit('@',1)[0]
		splitix = typename.index('[')
		typename = '%s%d%s' % (typename[:splitix+1], len(self), typename[splitix+1:])
		elemstr = ', '.join(repr(e) for e in self)
		return '%s {%s}' % (typename, elemstr)

	def __repr__(self):
		typename = str(type(self))
		splitix = typename.index('[')
		typename = '%s%d%s' % (typename[:splitix+1], len(self), typename[splitix+1:])
		return '<%s 0x%x>' % (typename, JavaObject._hprof_id.__get__(self))

class JavaClass(type):
	''' Base class for all Java classes. '''

	__slots__ = ()

	def __new__(mcs, name, supercls, static_attrs, iattr_names, iattr_types):
		assert '.' not in name
		assert '/' not in name or name.find('/') >= name.find('$$')
		assert '$' not in name or name.find('$') >= name.find('$$')
		assert ';' not in name
		assert isinstance(static_attrs, dict)
		assert isinstance(iattr_names, tuple)
		assert isinstance(iattr_types, tuple)
		assert len(iattr_names) == len(iattr_types)
		if supercls is None:
			supercls = JavaObject
		if mcs is JavaArrayClass and not isinstance(supercls, JavaArrayClass):
			slots = ('_hprof_ifieldvals', '_hprof_array_data')
			superclasses = (JavaArray,supercls)
		else:
			slots = ('_hprof_ifieldvals',)
			superclasses = (supercls,)
		cls = super().__new__(mcs, name, superclasses, {
			'__slots__': slots,
		})
		cls._hprof_sfields = static_attrs
		cls._hprof_ifieldix = {name:ix for ix, name in enumerate(iattr_names)}
		cls._hprof_ifieldtypes = iattr_types
		return cls

	def __init__(cls, name, supercls, static_attrs, iattr_names, iattr_types):
		del supercls, static_attrs, iattr_names, iattr_types # unused
		super().__init__(name, None, None)

	def __str__(cls):
		if cls.__module__:
			return str(cls.__module__) + '.' + cls.__name__
		return cls.__name__

	def __repr__(cls):
		return "<JavaClass '%s'>" % str(cls)

	def __instancecheck__(cls, instance):
		if type(instance) is Ref: # pylint: disable=unidiomatic-typecheck
			instance = Ref._target.__get__(instance)
		if type(instance) is JavaClass: # pylint: disable=unidiomatic-typecheck
			# not pretty...
			if str(cls) in ('java.lang.Object', 'java.lang.Class'):
				return True
		return super().__instancecheck__(instance)

	def __getattr__(cls, name):
		t = cls
		while t is not JavaObject:
			if name in t._hprof_sfields:
				return t._hprof_sfields[name]
			t, = t.__bases__
		raise AttributeError('type %r has no static attribute %r' % (cls, name))


class _DeferredArrayData(object):
	__slots__ = ('bytes', 'jtype')

	def __init__(self, jtype, raw_bytes):
		assert len(raw_bytes) % jtype.size == 0
		self.jtype = jtype
		self.bytes = raw_bytes

	def toarray(self):
		''' concretize to a real array '''
		from ._parsing import jtype
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
	''' Base class for all Java array classes. '''
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
				nxt = ctype(str(container) + '.' + p)
			else:
				nxt = ctype(p)
			setattr(container, p, nxt)
			container = nxt
	return container


_TYPECHAR_TO_NAME = {
	'Z': 'boolean',
	'C': 'char',
	'F': 'float',
	'D': 'double',
	'B': 'byte',
	'S': 'short',
	'I': 'int',
	'J': 'long',
}

_NAME_TO_TYPECHAR = {
	'boolean': 'Z',
	'char': 'C',
	'float': 'F',
	'double': 'D',
	'byte': 'B',
	'short': 'S',
	'int': 'I',
	'long': 'J',
}


def _create_class(container, name, supercls, staticattrs, iattr_names, iattr_types):
	# android hprofs may have slightly different class name format...
	if '.' in name:
		name = name.replace('.', '/')
	if name.endswith('[]'):
		a = 0
		while name.endswith('[]'):
			name = name[:-2]
			a += 1
		if name in _NAME_TO_TYPECHAR:
			name = _NAME_TO_TYPECHAR[name]
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
			name = _TYPECHAR_TO_NAME[name]

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
	if name[-1].startswith('$'):
		name = name[-1:]
	else:
		name = name[-1].split('$')
	if extra:
		name[-1] += extra
	name[-1] += nests * '[]'
	container = _get_or_create_container(container, name[:-1], JavaClassName) # pylint: disable=redefined-variable-type
	classname = _get_or_create_container(container, name[-1:], JavaClassName)
	name = name[-1]
	if nests:
		cls = JavaArrayClass(name, supercls, staticattrs, iattr_names, iattr_types)
	else:
		cls = JavaClass(name, supercls, staticattrs, iattr_names, iattr_types) # pylint: disable=redefined-variable-type
	if isinstance(container, JavaClassContainer):
		type.__setattr__(cls, '__module__', container)
	else:
		type.__setattr__(cls, '__module__', None)
	return classname, cls
