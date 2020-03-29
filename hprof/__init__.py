#!/usr/bin/env python3
# Copyright (C) 2019 Snild Dolkow
# Licensed under the LICENSE.

from . import error

import enum as _enum

class JavaType(_enum.Enum):
	object = 2
	boolean = 4
	char = 5
	float = 6
	double = 7
	byte = 8
	short = 9
	int = 10
	long = 11
jtype = JavaType # alternate name

from ._parsing import open, parse

from .heap import cast
