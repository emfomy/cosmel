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
		self.__lib = ctypes.cdll.LoadLibrary(lib_file)
		self.__obj = self.__lib.WordSeg_New()
		self.__lib.WordSeg_InitData.restype       = ctypes.c_bool
		self.__lib.WordSeg_ApplyFile.restype      = ctypes.c_bool
		self.__lib.WordSeg_ApplyList.restype      = ctypes.c_bool
		self.__lib.WordSeg_ApplyArticle.restype   = ctypes.c_bool
		self.__lib.WordSeg_GetResultBegin.restype = ctypes.c_wchar_p
		self.__lib.WordSeg_GetResultNext.restype  = ctypes.c_wchar_p
		self.__lib.WordSeg_GetUWBegin.restype     = ctypes.c_wchar_p
		self.__lib.WordSeg_GetUWNext.restype      = ctypes.c_wchar_p
		ret = self.__lib.WordSeg_InitData(self.__obj, ini_file.encode('utf-8'))
		if not ret:
			raise IOError(f'Loading {ini_file} failed.')

	def __del__(self):
		self.__lib.WordSeg_Destroy(self.__obj)

	def EnableLogger(self):
		self.__lib.WordSeg_EnableConsoleLogger(self.__obj)

	def ApplyFile(self, input_file, output_file):
		self.__lib.WordSeg_ApplyFile(self.__obj, input_file.encode('utf-8'), output_file.encode('utf-8'), None)

	def ApplyArticle(self, input_list):
		if len(input_list) == 0:
			return []
		in_arr = (ctypes.c_wchar_p * len(input_list))()
		in_arr[:] = input_list
		ret = self.__lib.WordSeg_ApplyArticle(self.__obj, len(input_list), in_arr)
		if ret == None:
			return []

		output_list = []
		out = self.__lib.WordSeg_GetResultBegin(self.__obj)
		while out != None:
			output_list.append(out)
			out = self.__lib.WordSeg_GetResultNext(self.__obj)
		return output_list


class CkipWsCore():
	"""The word segmentation driver core."""

	def __init__(self, lib_file, ini_file):
		self.__lib_file = lib_file
		self.__ini_file = ini_file
		self.__data = PyWordSeg(self.__lib_file, self.__ini_file)

	def reload(self):
		del self.__data
		self.__data = PyWordSeg(self.__lib_file, self.__ini_file)

	def apply_file(self, input_file, output_file):
		return self.__data.ApplyFile(input_file, output_file)

	def apply_article(self, sentences):
		return self.__data.ApplyArticle(sentences)

	def enable_logger(self):
		return self.__data.EnableLogger()


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
			self.__regexes.append((re.compile(rf'(\A|(?<=\n|　)){re.escape(seg[0])}\([A-Za-z0-9]*?\)'), seg[1], seg[0]))
		self.__regexes.append((re.compile(r'　□\(SP\)'), '', '□'))

		self.__core = CkipWsCore(lib_file, ini_file)
		print(f'Initialize CKIPWS with INI "{ini_file}" using lexicon "{lex_file}"')

		self.__ini_file = ini_file

	def ws_file(self, input_file, output_file, verbose=True):
		if verbose: print(f'Processing Word Segment on {input_file} to {output_file}')
		self.__core.apply_file(input_file, output_file)
		self.__core.reload()

	def ws_list(self, input_file, output_file, verbose=True):
		if verbose: print(f'Processing Word Segment on {input_file} to {output_file}')
		with open(input_file) as fin, open(output_file, 'w') as fout:
			fout.write('\n'.join(self.__core.apply_article(fin.readlines())))
		self.__core.reload()

	def ws_line(self, input_file, output_file, verbose=True):
		if verbose: print(f'Processing Word Segment on {input_file} to {output_file}')
		with open(input_file) as fin, open(output_file, 'w') as fout:
			lines = fin.readlines()
			n = str(len(lines))
			for i, line in enumerate(lines):
				if verbose: printr(f'{i+1:0{len(n)}}/{n}')
				fout.write('　'.join(self.__core.apply_article([line[i:i+80] for i in range(0, len(line), 80)]))+'\n')
		if verbose: print()
		self.__core.reload()

	def replace(self, input_file, output_file, input_encoding=None, output_encoding=None, verbose=True):
		with open(input_file, encoding=input_encoding) as fin, open(output_file, 'w', encoding=output_encoding) as fout:
			lines = fin.read()
			for regex in self.__regexes:
				if verbose: printr(regex[2])
				lines = regex[0].sub(regex[1], lines)
			fout.write(lines)
