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
		article_path (str):    the path to the folder containing word segmented article files.
		mention_path (str):    the path to the folder containing mention files.
		repo (:class:`.Repo`): the product repository class.
		parts (list):          the list of article/mention parts.

	Notes:
		* Load all articles from ``article_path``/``part`` for all ``part`` in ``parts``.
		* Load all mentions from ``mention_path``/``part`` for all ``part`` in ``parts``.
	"""

	def __init__(self, article_path, mention_path, repo, parts=['']):
		self.__article_set                = ArticleSet(article_path, parts=parts)
		self.__id_to_article              = Id2Article(self.__article_set)

		self.__mention_bundle_set         = MentionBundleSet(article_path, mention_path, self.__article_set, repo)
		self.__mention_set                = MentionSet(self.__mention_bundle_set)
		self.__article_to_mention_bundle  = Article2MentionBundle(self.__mention_bundle_set)
		self.__brand_head_to_mention_list = BrandHead2MentionList(self.__mention_set)

	@property
	def article_set(self):
		""":class:`.ArticleSet`: the article set."""
		return self.__article_set

	@property
	def id_to_article(self):
		""":class:`.Id2Article`: the dictionary maps ID to article."""
		return self.__id_to_article

	@property
	def mention_set(self):
		""":class:`.MentionSet`: the mention set."""
		return self.__mention_set

	@property
	def mention_bundle_set(self):
		""":class:`.MentionBundleSet`: the mention bundle set."""
		return self.__mention_bundle_set

	@property
	def article_to_mention_bundle(self):
		""":class:`.Article2MentionBundle`: the dictionary maps article to mention list."""
		return self.__article_to_mention_bundle

	@property
	def brand_head_to_mention_list(self):
		""":class:`.BrandHead2MentionList`: the dictionary maps brand and head to mention list."""
		return self.__brand_head_to_mention_list
