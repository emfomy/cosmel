#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import collections.abc
import os

from styleme.util import *

class Article(collections.abc.Sequence):
	"""The article object (contains list of sentences).

	* Item: the word-segmented sentence (:class:`.WsWords`)

	Args:
		file_path (str): the path to the article.
	"""

	@staticmethod
	def path_to_aid(path):
		"""str: Convert file path to article ID."""
		norm_path = os.path.normpath(path)
		return os.path.basename(os.path.dirname(norm_path)) + '/' + os.path.basename(norm_path).split('.')[0]

	def __init__(self, file_path):
		super().__init__()

		with open(file_path) as fin:
			self.__data = [WsWords(line) for line in fin]

		self.__aid = Article.path_to_aid(file_path)
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

	def __roledstr__(self):
		return '\n'.join(map(roledstr, self.__data))

	def __roledtxtstr__(self):
		return '\n'.join(map(roledtxtstr, self.__data))

	def __hash__(self):
		return hash(self.aid)

	@property
	def aid(self):
		"""str: the article ID (containg folder and author name)."""
		return self.__aid

	@property
	def path(self):
		"""str: the related file path."""
		return self.__path

	@property
	def parsed(self):
		""":class:`.ParsedArticle`: the parsed article of this article."""
		return self.__parsed

	@property
	def bundle(self):
		""":class:`.MentionBundle`: the mention bundle of this article."""
		return self.__bundle

	def save(self, file_path, method):
		"""Save the article to file.

			Args:
				method: one of :func:`str`, :func:`txtstr`, :func:`roledstr`, :func:`roledtxtstr`.

		"""
		os.makedirs(os.path.dirname(file_path), exist_ok=True)
		with open(file_path, 'w') as fout:
			fout.write(method(self)+'\n')


class ArticleSet(collections.abc.Collection):
	"""The set of articles.

	* Item: the article object (:class:`.Article`)

	Args:
		article_root (str): the path to the folder containing data files.
		parts (list):       the list of article/mention parts.

	Notes:
		* Load all articles from ``article_root``/``part`` for all ``part`` in ``parts``.
	"""

	def __init__(self, article_root, parts=[''], skips=[]):
		super().__init__()
		files = grep_files(article_root, parts)
		files = [file for file in files if Article.path_to_aid(file) not in skips]
		n = str(len(files))
		self.__data = [self.__article(file, i, n) for i, file in enumerate(files)]
		self.__path = article_root
		print()

	@classmethod
	def __article(self, file, i, n):
		printr(f'{i+1:0{len(n)}}/{n}\tReading {file}')
		return Article(file)

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


class Id2Article(collections.abc.Mapping):
	"""The dictionary maps article ID to article object.

	* Key:  the article ID (str).
	* Item: the article object (:class:`.Article`).

	Args:
		article_set (:class:`.ArticleSet`): the article set.
	"""

	def __init__(self, article_set):
		super().__init__()
		self.__data = dict()
		for article in article_set:
			assert article.aid not in self.__data
			self.__data[article.aid] = article

	def __contains__(self, key):
		return key in self.__data

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)
