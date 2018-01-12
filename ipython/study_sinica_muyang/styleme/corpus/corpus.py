#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

from styleme.util import *
from styleme.repo import *
from styleme.corpus.article import *


class Corpus:
	"""The corpus class.

	Args:
		article_ws_path (str): the path to the folder containing word segmented article files.
		repo (:class:`.Repo`): the product repository class.
	"""

	def __init__(self, article_ws_path, repo):
		self.__articles   = ArticleSet(article_ws_path)
		self.__id2article = Id2Article(self.__articles)

	@property
	def articles(self):
		""":class:`.ArticleSet` --- the article set."""
		return self.__articles

	@property
	def id2article(self):
		""":class:`.Id2Article` --- the dictionary maps ID to article."""
		return self.__id2article