#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import collections.abc
import os

from styleme.util import *


class Article(collections.abc.Sequence):
	"""The article class (contains list of sentences).

	* Item: the word-segmented sentence (:class:`.WsWords`)

	Args:
		file_path (str): the path to the article.
	"""

	def __init__(self, file_path):
		super().__init__()
		printr('Reading {}'.format(file_path))
		with open(file_path) as fin:
			self.__data = [WsWords(line) for line in fin]

		self.__a_id = os.path.basename(file_path).split('.')[0]
		self.__path = file_path

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

	def __repr__(self):
		return '\n'.join(map(repr, self.__data))

	def __txtstr__(self):
		return '\n'.join(map(txtstr, self.__data))

	@property
	def a_id(self):
		"""str: the article ID (with leading author name and underscore)."""
		return self.__a_id

	@property
	def path(self):
		"""str: the related file path."""
		return self.__path


class ArticleSet(collections.abc.Collection):
	"""The set of articles.

	* Item: the article (:class:`.Article`)

	Args:
		article_path (str): the path to the folder containing data files.
	"""

	def __init__(self, article_path):
		super().__init__()
		self.__data = [Article(file) for file in grep_files(article_path)]
		print()

	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)


class Path2Article(collections.abc.Mapping):
	"""The dictionary maps file path to article.

	* Key:  the related file path of the article (str).
	* Item: the article (:class:`.Article`).

	Args:
		article_set (:class:`.ArticleSet`): the article set.
	"""

	def __init__(self, article_set):
		super().__init__()
		self.__data = dict()
		for article in article_set:
			assert article.path not in self.__data
			self.__data[article.path] = article

	def __contains__(self, key):
		return key in self.__data

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)
