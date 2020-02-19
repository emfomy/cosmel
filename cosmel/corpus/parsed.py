#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <http://muyang.pro>'
__copyright__ = 'Copyright 2017-2018'


import collections.abc
import os

from cosmel.util import *
from cosmel.corpus.article import *

class ParsedArticle(collections.abc.Sequence):
	"""The parsed article object (contains list of sentences).

	* Item: the parsed sentence (str)

	Args:
		file_path (str): the path to the article.
	"""

	def __init__(self, file_path, article):
		super().__init__()

		with open(file_path) as fin:
			self.__data = [self.__load_line(line) for line in fin]

		self.__article = article
		self.__path    = file_path

	@staticmethod
	def __load_line(line):
		line = line.lstrip('#1:1.[0] ')
		line = line.split('#', 1)[0]
		return line

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

	def __hash__(self):
		return hash(self.aid)

	@property
	def article(self):
		""":class:`.Article`: the article of this bundle."""
		return self.__article

	@property
	def aid(self):
		"""str: the article ID (with leading author name and underscore)."""
		return self.__article.aid

	@property
	def path(self):
		"""str: the related file path."""
		return self.__path


class ParsedArticleSet(collections.abc.Collection):
	"""The set of parsed articles.

	* Item: the parsed article object (:class:`.ParsedArticle`)

	Args:
		parsed_root (str):                  the path to the folder containing parsed article files.
		article_set (:class:`.ArticleSet`): the set of articles.

	Notes:
		* Load all articles from ``parsed_root``/``part`` for all ``part`` in ``parts``.
	"""

	def __init__(self, parsed_root, article_set):
		super().__init__()
		n = str(len(article_set))
		self.__data = [self.__parsed_article(article, article_set.path, parsed_root, i, n) for i, article in enumerate(article_set)]
		self.__path = parsed_root
		print()

	@staticmethod
	def __parsed_article(article, article_root, parsed_root, i, n):
		file_path = transform_path(article.path, article_root, parsed_root, '.parse')
		printr(f'{i+1:0{len(n)}}/{n}\tReading {file_path[-80:]}')
		parsed = ParsedArticle(file_path, article)
		article._Article__parsed = parsed
		return parsed

	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	@property
	def path(self):
		"""str: the root path of the articles."""
		return self.__path


class Id2ParsedArticle(collections.abc.Mapping):
	"""The dictionary maps article ID to parsed article.

	* Key:  the article ID (str).
	* Item: the parsed article (:class:`.ParsedArticle`).

	Args:
		id_to_article (:class:`.Id2Article`): the dictionary maps article ID to article object.
	"""

	def __init__(self, id_to_article):
		super().__init__()
		self.__data  = id_to_article

	def __contains__(self, key):
		return key in self.__data

	def __getitem__(self, key):
		return self.__data[key].parsed

	def __iter__(self):
		return iter(map(self.__data, operator.attrgetter('parsed')))

	def __len__(self):
		return len(self.__data)
