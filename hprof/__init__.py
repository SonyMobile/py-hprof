#!/usr/bin/env python3
# Copyright (C) 2019 Snild Dolkow
# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

import enum as _enum

# pylint: disable=wrong-import-position
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
jtype = JavaType # pylint: disable=invalid-name

from . import error
from ._parsing import open, parse # pylint: disable=redefined-builtin
from .heap import cast
