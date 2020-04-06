#!/usr/bin/env python3
# Copyright (C) 2020 Sony Mobile Communications Inc.
# Licensed under the LICENSE.

import inspect
import sys
import html

class tag(object):
	def __init__(self, tagname, **attrs):
		self.name = tagname
		self.attrs = attrs

	def __enter__(self):
		print('<', end='')
		print(self.name, end='')
		if self.attrs:
			for name, value in self.attrs.items():
				print(' ', end='')
				print(name, end='')
				print('="', end='')
				print(html.escape(value), end='')
				print('"', end='')
		print('>', end='')
		return self

	def __exit__(self, exctype, excval, tb):
		print('</%s>' % self.name, end='')

	def text(self, string):
		print(html.escape(string), end='')

def div(htmlclass):
	return tag('div', **{'class':htmlclass})

def pathspan(pathstack):
	if pathstack:
		with tag('span', **{'class':'path'}) as span:
			path = '.'.join(pathstack)
			span.text(path + '.')

def inlinelabel(namestack):
	with tag('span', **{'class':'inlinelabel'}) as span:
		pathspan(namestack[:-1])
		span.text(namestack[-1])
		span.text(': ')

def argspan(fun):
	with tag('span', **{'class':'args'}) as span:
		span.text(' (')
		params = inspect.signature(fun).parameters
		span.text(', '.join(s for i, s in enumerate(params) if s != 'self' or i != 0))
		span.text(')')

def anchor(namestack):
	joined = '.'.join(namestack)
	return tag('a', name=joined, href='#' + joined)

def _interesting(pything):
	return (inspect.ismodule(pything)
		or inspect.isfunction(pything)
		or inspect.ismethod(pything)
		or inspect.isclass(pything)
		or isinstance(pything, property)
		or isinstance(pything, classmethod)
		or isinstance(pything, staticmethod)
	)

class Generator(object):
	def __init__(self, title, rootname, root):
		self.title = title
		self.rootname = rootname
		self.root = root
		self.labels = {} # only used for modules
		self.order = {}

	def generate(self):
		with tag('h1') as hdr:
			hdr.text(self.title)
		self._doc(self.root)
		self._members((self.rootname,), self.root)

	def _generate(self, namestack, pything):
		if inspect.ismodule(pything):
			with div('module'):
				label = self.labels.get(pything)
				with tag('h2') as hdr:
					with anchor(namestack):
						if label is not None:
							hdr.text(label)
							hdr.text(' (')
						pathspan(namestack[:-1])
						hdr.text(namestack[-1])
						if label is not None:
							hdr.text(')')
				self._doc(pything)
				self._members(namestack, pything)
		elif inspect.isclass(pything):
			with div('class'):
				with tag('h3') as hdr:
					with anchor(namestack):
						pathspan(namestack[:-1])
						hdr.text(namestack[-1])
						argspan(pything.__init__)
				self._doc(pything)
				self._members(namestack, pything)
		elif inspect.isfunction(pything):
			with div('function'):
				with tag('h4') as hdr:
					with anchor(namestack):
						pathspan(namestack[:-1])
						hdr.text(namestack[-1])
						argspan(pything)
				self._doc(pything)
		elif isinstance(pything, property):
			with div('property'):
				self._doc(pything, namestack)
		else:
			raise Exception('unhandled', pything)

	def _members(self, namestack, pything):
		order = self.order.get(pything, ())
		def memberkey(pair):
			if type(pair) is not tuple:
				name = member = pair
			else:
				name, member = pair
			typeorder = 0
			if inspect.isfunction(member):
				typeorder = 1
			elif inspect.isclass(member):
				typeorder = 2
			elif inspect.ismodule(member):
				typeorder = 3
			try:
				return (order.index(member), typeorder, name)
			except ValueError:
				return (len(order), typeorder, name)
		things = inspect.getmembers(pything, _interesting) + [x for x in order if type(x) is str]
		for thing in sorted(things, key=memberkey):
			if type(thing) is tuple:
				name, member = thing
				if not name.startswith('_'):
					self._generate(namestack + (name,), member)
			else:
				with tag('h2') as hdr:
					with anchor((thing.replace(' ', '_'),)):
						hdr.text(thing)

	def _doc(self, pything, label=None):
		with div('docstr'):
			clean = inspect.getdoc(pything)
			if clean is None:
				clean = '(not documented)'
			iterator = iter(clean.split('\n'))
			for line in iterator:
				if not line.strip():
					continue
				if line.startswith('>>>'):
					if label:
						with tag('p') as paragraph:
							inlinelabel(label)
						label = None
					with tag('pre'):
						with tag('code') as codenode:
							while line:
								if not line.strip():
									break # end of the code example.
								line = line.rsplit('# doctest:', 1)[0]
								codenode.text(line)
								codenode.text('\n')
								try:
									line = next(iterator)
								except StopIteration:
									line = None
				else:
					printmember = False
					with tag('p') as paragraph:
						if label:
							inlinelabel(label)
						label = None
						while line:
							parts = line.split(maxsplit=2)
							if len(parts) >= 2 and parts[1] == '--':
								printmember = True
								break
							paragraph.text(line)
							paragraph.text(' ')
							try:
								line = next(iterator)
							except StopIteration:
								line = None
					if printmember:
						with tag('p') as paragraph:
							inlinelabel((parts[0],))
							paragraph.text(parts[2])
			if label:
				with tag('p') as paragraph:
					inlinelabel(label)

if __name__ == '__main__':
	import hprof
	with tag('html'):
		with tag('head'):
			with tag('title') as title:
				title.text('hprof docs')
			with tag('style', type='text/css') as css:
				print('''
body {
	font-family: sans-serif;
	background-color: #666666;
	color: #ffffff;
}

div#content {
	margin:auto;
	width: 50em;
}

.class, #content>.docstr, #content>.module>.docstr, #content>.module>.function, #content>.function {
	padding: 0.1em;
	padding-left: 1em;
	padding-right: 1em;
	background-color: #fcfcfc;
	margin-bottom: 1em;
	color: #222222;
}

h3, h4 {
	background-color: #eeeeee;
	margin-bottom: 0;
}

.function p:first-child, .class p:first-child {
	margin-top: 0.2em;
}

.path {
	color: #777777;
	font-weight: normal;
}

.module>h2 .path {
	color: #999999;
}

.inlinelabel {
	font-weight: bold;
}

.args {
	color: #444444;
	font-size: 0.8em;
}

pre {
	color: #333333;
}

a[name] {
	text-decoration:none;
	outline:none;
	color:inherit;
}

''')
		with tag('body'):
			with tag('div', id='content'):
				gen = Generator('The hprof library', 'hprof', hprof)

				gen.labels[hprof.heap] = 'Java Heap Model'
				#gen.labels[hprof.record] = 'Records'
				gen.order[hprof] = (
					hprof.open, hprof.parse,
				)
				#gen.order[hprof.HprofFile] = (
				#	hprof.HprofFile.records, hprof.HprofFile.dumps, hprof.HprofFile.close,
				#)
				gen.generate()
