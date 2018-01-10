#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import itertools
import re
import subprocess

from styleme.util.core import *


class WordSegment():
	"""The word segmentation driver"""

	def __init__(self, ini_file, lex_files, extra_files, input_encoding=None, output_encoding='big5'):
		with open(ini_file, encoding=input_encoding) as fin:
			lines = fin.read().splitlines()
			idx = lines.index('[CTextLexicon]')
			if idx < 0:
				raise Exception('INI file "{}" contains no [CTextLexicon]'.format(ini_file))
			for line in lines[idx+1::]:
				if '[' == line[0]:
					raise Exception('INI file "{}" contains no [CTextLexicon] FileName'.format(ini_file))
				if 'FileName' in line:
					lex_file = line.split('=')[1]
					break

		with open(lex_file, 'w', encoding=output_encoding) as fout:
			for file in lex_files + extra_files:
				with open(file, encoding=input_encoding) as fin:
					fout.write(fin.read())

		self.__regexes = []
		for line in itertools.chain.from_iterable(map(open, lex_files)):
			if line.strip() == '':
				continue
			seg = line.strip().split('\t')
			self.__regexes.append((\
					re.compile(r'((\A|\n|　){})\([A-Za-z0-9]*\)'.format(re.escape(seg[0]))), \
					r'\1({})'.format(re.escape(seg[1])), seg[0]))
		self.__regexes.append((re.compile(r'　□\(SP\)'), '', '□'))

		print('Initialize CKIPWS with INI "{}" using lexicon "{}"'.format(ini_file, lex_file))

		self.__ini_file  = ini_file
		self.__lex_file  = lex_file
		self.__lex_files = lex_files

	def __call__(self, input_file, output_file):
		# subprocess.call('CKIPWSTester {} {} {}'.format(self.__ini_file, input_file, output_file), shell=True)
		print('CKIPWSTester {} {} {}'.format(self.__ini_file, input_file, output_file))
		print('Processing Word Segment on {} to {}'.format(input_file, output_file))
		input("Press Enter to continue...")

	def replace(self, input_file, output_file, input_encoding='utf-16-le', output_encoding=None):
		with open(input_file, encoding=input_encoding) as fin, open(output_file, 'w', encoding=output_encoding) as fout:
			lines = fin.read()
			for regex in self.__regexes:
				printr(regex[2])
				lines = regex[0].sub(regex[1], lines)
			fout.write(lines)