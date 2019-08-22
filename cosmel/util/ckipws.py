#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import itertools
import os
import re
import tempfile

from ckipnlp.ws import CkipWs as Core

from cosmel.util.core import *


class CkipWs():
	"""The word segmentation driver."""

	def __init__(self, lex_files, compound_files, input_encoding=None, output_encoding=None, verbose=True):

		self.lex_file_obj = tempfile.NamedTemporaryFile(mode='w', encoding=output_encoding)
		lex_file = self.lex_file_obj.name
		if verbose: print(f'Generating lexicon "{lex_file}"')

		for file in lex_files:
			if verbose: print(f'... from lexicon "{file}"')
			with open(file, encoding=input_encoding) as fin:
				self.lex_file_obj.write(fin.read()+'\n')
		self.lex_file_obj.flush()

		self.__regexes = []
		for line in itertools.chain.from_iterable(map(open, compound_files)):
			if line.strip() == '': continue
			seg = line.strip().split('\t')
			self.__regexes.append((re.compile(rf'(\A|(?<=\n|　)){re.escape(seg[0])}\([A-Za-z0-9]*?\)'), seg[1], seg[0]))
		self.__regexes.append((re.compile(r'　□\(SP\)'), '', '□'))

		if verbose: print(f'Initialize CKIPWS using lexicon "{lex_file}"')
		self.__core = Core(new_style_format=True, lexfile=lex_file)

	def ws_file(self, input_file, output_file, verbose=True):
		if verbose: print(f'Processing Word Segment on {input_file} to {output_file}')
		self.__core.apply_file(input_file, output_file)

	def ws_list(self, input_file, output_file, verbose=True):
		if verbose: print(f'Processing Word Segment on {input_file} to {output_file}')
		with open(input_file) as fin, open(output_file, 'w') as fout:
			fout.write('\n'.join(self.__core.apply_list(fin.readlines())))

	def ws_line(self, input_file, output_file, verbose=True):
		if verbose: print(f'Processing Word Segment on {input_file} to {output_file}')
		with open(input_file) as fin, open(output_file, 'w') as fout:
			lines = fin.readlines()
			n = str(len(lines))
			for i, line in enumerate(lines):
				if verbose: printr(f'{i+1:0{len(n)}}/{n}\t{line[:8].strip()}...')
				fout.write('　'.join(self.__core.apply_list([line[i:i+80] for i in range(0, len(line), 80)]))+'\n')
		if verbose: print()

	def replace(self, input_file, output_file, input_encoding=None, output_encoding=None, verbose=True):
		with open(input_file, encoding=input_encoding) as fin, open(output_file, 'w', encoding=output_encoding) as fout:
			lines = fin.read()
			for regex in self.__regexes:
				if verbose: printr(regex[2])
				lines = regex[0].sub(regex[1], lines)
			fout.write(lines)
