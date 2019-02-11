#!/usr/bin/env python3
#coding=utf8

import os as _os
import sys as _sys

_koko  = _os.path.dirname(__file__)
_soko  = _os.path.join(_koko, '..')
_asoko = _os.path.abspath(_soko)

_sys.path.insert(0, _asoko)

def find(relpath):
	p = _os.path.join(_koko, relpath)
	return _os.path.abspath(p)

import hprof
