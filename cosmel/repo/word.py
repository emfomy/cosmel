#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <http://muyang.pro>'
__copyright__ = 'Copyright 2017-2018'


import collections.abc

from cosmel.util import *


class WordSet(collections.abc.Collection):
	"""The set of words.

	* Item: the word (str).

	Args:
		lex_file (str): the path to the lexicon file.
	"""

	def __init__(self, lex_file):
		super().__init__()
		self.__data = set()
		with open(lex_file) as fin:
			for line in fin:
				if line.strip() == '': continue
				self.__data.add(line.strip().split('\t')[0])

	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def __str__(self):
		return '\n'.join(map(str, self.__data))

	def __repr__(self):
		return '\n'.join(map(repr, self.__data))


class HeadSet(WordSet):
	"""The set of head words.

	* Item: the head word (str).

	Args:
		repo_root (str): the path to the folder containing data files.
	"""
	def __init__(self, repo_root):
		super().__init__(f'{repo_root}/head.txt')


class InfixSet(WordSet):
	"""The set of infix words.

	* Item: the infix word (str).

	Args:
		repo_root (str): the path to the folder containing data files.
	"""
	def __init__(self, repo_root):
		super().__init__(f'{repo_root}/infix.txt')
