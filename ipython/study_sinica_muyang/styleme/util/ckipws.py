#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import ctypes
import itertools
import os
import re
import sys

from styleme.util.core import *

class PyWordSeg():

	def __init__(self, lib_file, ini_file):
		self.lib = ctypes.cdll.LoadLibrary(lib_file)
		self.lib.WordSeg_InitData.restype = ctypes.c_bool
		self.lib.WordSeg_ApplyList.restype = ctypes.c_bool
		self.lib.WordSeg_GetResultBegin.restype = ctypes.c_wchar_p
		self.lib.WordSeg_GetResultNext.restype = ctypes.c_wchar_p
		self.obj = self.lib.WordSeg_New()
		ret = self.lib.WordSeg_InitData(self.obj, ini_file.encode('utf-8'))
		if not ret:
			raise IOError(f'Loading {ini_file} failed.')

	def __del__(self):
		self.lib.WordSeg_Destroy(self.obj)

	def EnableLogger(self):
		self.lib.WordSeg_EnableConsoleLogger(self.obj)

	def ApplyList(self, input_list):
		if len(input_list) == 0:
			return []
		in_arr = (ctypes.c_wchar_p * len(input_list))()
		in_arr[:] = input_list
		ret = self.lib.WordSeg_ApplyList(self.obj, len(input_list), in_arr)
		if ret == None:
			return []

		output_list = []
		out = self.lib.WordSeg_GetResultBegin(self.obj)
		while out != None:
			output_list.append(out)
			out = self.lib.WordSeg_GetResultNext(self.obj)
		return output_list


class CkipWsCore():
	"""The word segmentation driver core."""

	def __init__(self, lib_file, ini_file):
		self.__data = PyWordSeg(lib_file, ini_file)

	def __call__(self, sentences):
		return self.__data.ApplyList(sentences)


class CkipWs():
	"""The word segmentation driver."""

	def __init__(self, lib_file, ini_file, lex_files, compound_files, input_encoding=None, output_encoding=None):

		with open(ini_file, encoding=input_encoding) as fin:
			lines = fin.read().splitlines()
			idx = lines.index('[CTextLexicon]')
			if idx < 0:
				raise Exception(f'INI file "{ini_file}" contains no [CTextLexicon]')
			for line in lines[idx+1::]:
				if '[' == line[0]:
					raise Exception(f'INI file "{ini_file}" contains no [CTextLexicon] FileName')
				if 'FileName' in line:
					lex_file = line.split('=')[1]
					break

		os.makedirs(os.path.dirname(lex_file), exist_ok=True)
		with open(lex_file, 'w', encoding=output_encoding) as fout:
			for file in lex_files:
				with open(file, encoding=input_encoding) as fin:
					fout.write(fin.read()+'\n')

		self.__regexes = []
		for line in itertools.chain.from_iterable(map(open, compound_files)):
			if line.strip() == '': continue
			seg = line.strip().split('\t')
			self.__regexes.append((re.compile(rf'(\A|(?<=\n|　)){re.escape(seg[0])}\([A-Za-z0-9]*\)'), seg[1], seg[0]))
		self.__regexes.append((re.compile(r'　□\(SP\)'), '', '□'))

		self.__core = CkipWsCore(lib_file, ini_file)
		print(f'Initialize CKIPWS with INI "{ini_file}" using lexicon "{lex_file}"')

		self.__ini_file = ini_file

	def ws(self, input_file, output_file):
		print(f'Processing Word Segment on {input_file} to {output_file}')
		with open(input_file) as fin, open(output_file, 'w') as fout:
			fout.write('\n'.join(self.__core(fin.readlines())))

	def ws_line(self, input_file, output_file):
		print(f'Processing Word Segment on {input_file} to {output_file}')
		with open(input_file) as fin, open(output_file, 'w') as fout:
			lines = fin.readlines()
			n = len(lines)
			for i, line in enumerate(lines):
				printr(f'{i}/{n}')
				fout.write(self.__core([line])[0]+'\n')
		print()

	def replace(self, input_file, output_file, input_encoding=None, output_encoding=None, verbose=True):
		with open(input_file, encoding=input_encoding) as fin, open(output_file, 'w', encoding=output_encoding) as fout:
			lines = fin.read()
			for regex in self.__regexes:
				if verbose: printr(regex[2])
				lines = regex[0].sub(regex[1], lines)
			fout.write(lines)
