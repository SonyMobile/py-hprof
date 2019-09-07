class Heap(object):
	__slots__ = ('objects')

	def __init__(self):
		self.objects = {}


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
		return getattr(r, name).__get__(t)

	def __dir__(self):
		out = ()
		r = Ref._reftype.__get__(self)
		while r is not JavaObject:
			out += r.__slots__
			r, = r.__bases__
		return tuple(set(out))

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


class JavaPackage(object):
	def __init__(self, name):
		self.name = name

	def __str__(self):
		return self.name

	def __repr__(self):
		return "<JavaPackage '%s'>" % self.name


class JavaObject(object):
	__slots__ = (
		'_hprof_id',       # object id
	)

	def __repr__(self):
		objid = JavaObject._hprof_id.__get__(self)
		return '<%s 0x%x>' % (type(self), objid)

	def __dir__(self):
		out = ()
		t = type(self)
		while t is not JavaObject:
			out += t.__slots__
			t, = t.__bases__
		return tuple(set(out))


def _javaclass_init(self, objid):
	JavaObject._hprof_id.__set__(self, objid)


class JavaClass(type):
	__slots__ = ()
	def __new__(meta, name, supercls, instance_attrs):
		if supercls is None:
			supercls = JavaObject
		return super().__new__(meta, name, (supercls,), {
			'__init__': _javaclass_init,
			'__slots__': instance_attrs,
		})

	def __init__(meta, name, supercls, instance_attrs):
		assert '.' not in name
		super().__init__(name, None, None)

	def __str__(self):
		if self.__module__:
			return self.__module__ + '.' + self.__name__
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

def _get_or_create_pkg(container, path):
	assert path != ''
	assert '/' not in path
	assert ';' not in path
	for p in path.split('.'):
		if hasattr(container, p):
			container = getattr(container, p)
			assert isinstance(container, JavaPackage)
		else:
			if isinstance(container, JavaPackage) or isinstance(container, JavaClass):
				next = JavaPackage(str(container) + '.' + p)
			else:
				next = JavaPackage(p)
			setattr(container, p, next)
			container = next
	return container

def _add_class(container, name, supercls, slots):
	assert '/' not in name
	assert ';' not in name
	parts = name.rsplit('.', 1)
	if len(parts) == 2:
		container = _get_or_create_pkg(container, parts[0])
		name = parts[1]
	if hasattr(container, name):
		raise ValueError('%r.%s already exists' % (container, name))
	cls = JavaClass(name, supercls, slots)
	if type(container) is JavaPackage:
		cls.__module__ = str(container)
	else:
		cls.__module__ = None
	setattr(container, name, cls)
