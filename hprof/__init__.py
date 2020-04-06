#!/usr/bin/env python3
# Copyright (C) 2019 Snild Dolkow
# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

'''Conveniently read Java/Android .hprof files.

>>> import hprof
>>> hf = hprof.open('testdata/example-java.hprof.bz2') # doctest: +SKIP
>>> heap, = hf.heaps

Class lookups by name:

>>> car_cls, = heap.classes['com.example.cars.Car']
>>> car_cls # doctest: +ELLIPSIS
<JavaClass 'com.example.cars.Car'>

Finding all instances of a class, reading object attributes, instanceof:

>>> vehicles = heap.all_instances('com.example.cars.Vehicle')
>>> vehicles = sorted(vehicles, key=lambda v: str(v.make))
>>> for v in vehicles: # doctest: +ELLIPSIS
...     print(type(v), v.make, isinstance(v, car_cls))
com.example.cars.Bike Axes False
com.example.cars.Bike Fånark False
com.example.cars.Car Lolvo True
com.example.cars.Limo Stretch True
com.example.cars.Car Toy Yoda True

Reading object arrays:

>>> carex, = heap.all_instances('com.example.Cars')
>>> carex # doctest: +ELLIPSIS
<com.example.Cars 0x...>
>>> carex.vehicles # doctest: +ELLIPSIS
<com.example.cars.Vehicle[5] 0x...>
>>> print(carex.vehicles) # doctest: +ELLIPSIS
Vehicle[5] {<com.example.cars.Car 0x...>, <com.example...}
>>> carex.vehicles[0] # doctest: +ELLIPSIS
<com.example.cars.Car 0x...>
>>> print(carex.vehicles[0]) # doctest: +ELLIPSIS
Car@...
>>> print(carex.vehicles[0].make)
Lolvo
'''

from . import error
from ._parsing import open, parse # pylint: disable=redefined-builtin
from .heap import cast
