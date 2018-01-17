#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

from styleme.util import *
from styleme.repo import *
from styleme.corpus.article import *
from styleme.corpus.mention import *


class Corpus:
	"""The corpus class.

	Args:
		article_path (str): the path to the folder containing word segmented article files.
		mention_path (str): the path to the folder containing mention files.
		repo (:class:`.Repo`): the product repository class.
	"""

	def __init__(self, article_path, mention_path, repo):
		self.__articles           = ArticleSet(article_path)
		self.__path2article       = Path2Article(self.__articles)
		self.__mentions           = MentionSet(article_path, mention_path, self.__articles, repo)
		self.__brandhead2mentions = BrandHead2Mentions(self.__mentions)

	@property
	def articles(self):
		""":class:`.ArticleSet`: the article set."""
		return self.__articles

	@property
	def path2article(self):
		""":class:`.Path2Article`: the dictionary maps file path to brand."""
		return self.__path2article

	@property
	def mentions(self):
		""":class:`.MentionSet`: the mention set."""
		return self.__mentions

	@property
	def brandhead2mentions(self):
		""":class:`.BrandHead2Mentions`: the dictionary maps brand and head to mention list."""
		return self.__brandhead2mentions
