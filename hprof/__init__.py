# Copyright (C) 2019 Sony Mobile Communications Inc.
# Licensed under the LICENSE

'''Conveniently read Java/Android .hprof files.

>>> import hprof
>>> hf = hprof.open('tests/java.hprof')
>>> dump, = hf.dumps()

Class lookups by name:

>>> car_cls = dump.get_class('com.example.cars.Car')
>>> car_cls # doctest: +ELLIPSIS
Class(name=com.example.cars.Car, id=0x...)

Finding all instances of a class, reading object attributes, instanceof:

>>> vehicles = dump.find_instances('com.example.cars.Vehicle')
>>> vehicles = sorted(vehicles, key=lambda v: str(v.make))
>>> for v in vehicles:
...     print(v.hprof_class, v.make, v.hprof_instanceof(car_cls))
com.example.cars.Bike Descent False
com.example.cars.Bike Fånark False
com.example.cars.Car Lolvo True
com.example.cars.Limo Stretch True
com.example.cars.Car Yotoya True

Reading object arrays:

>>> carex, = dump.find_instances('com.example.cars.CarExample')
>>> carex # doctest: +ELLIPSIS
Object(class=com.example.cars.CarExample, id=0x...)
>>> carex.objs # doctest: +ELLIPSIS
ObjectArray(class=java.lang.Object[], id=0x..., length=5)
>>> print(carex.objs) # doctest: +ELLIPSIS
Object[5] {Car(id=0x...), ...}
>>> carex.objs[0] # doctest: +ELLIPSIS
Object(class=com.example.cars.Car, id=0x...)
>>> print(carex.objs[0]) # doctest: +ELLIPSIS
Car(id=0x...)
'''

from ._binary import HprofFile, open
from ._dump import Dump, Heap
from ._errors import Error, FileFormatError, EofError, RefError, ClassNotFoundError, FieldNotFoundError, UnfamiliarStringError
from ._types import JavaType

from . import heap
from . import record
