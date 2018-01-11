#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import os
import collections.abc

from styleme.util import *


class Article(collections.abc.Sequence):
	"""The article class (contains list of sentences).

	Args:
		file_path (str): the path to the article.
	"""

	def __init__(self, file_path):
		super().__init__()
		self.__data = list()
		with open(file_path) as fin:
			for line in fin:
				self.__data.append(WsWords(line))

		self.__a_id = os.path.basename(file_path).split('.')[0]
		self.__path = os.path.abspath(file_path)

	def __contains__(self, item):
		return item in self.__data

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def __str__(self):
		return '\n'.join(map(str, self.__data))

	def __textstr__(self):
		return '\n'.join(map(textstr, self.__data))

	@property
	def a_id(self):
		"""str --- the article ID."""
		return self.__a_id

	@property
	def path(self):
		"""str --- the file path."""
		return self.__path


class ArticleSet(collections.abc.Collection):
	"""The set of articles.

	Args:
		article_path (str): the path to the folder containing data files.
	"""

	def __init__(self, article_path):
		super().__init__()
		self.__data = list()
		for file in grep_files(article_path):
			printr('Reading {}'.format(file))
			self.__data.append(Article(file))
		print()

	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)
