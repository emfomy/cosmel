#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


from styleme.util import *
from styleme.repo import *
from styleme.corpus.article import *
from styleme.corpus.mention import *


class Corpus:
	"""The corpus class.

	Args:
		article_root (str):    the path to the folder containing word segmented article files.
		mention_root (str):    the path to the folder containing mention files.
		parts (list):          the list of article/mention parts.

	Notes:
		* Load all articles from ``article_root``/``part`` for all ``part`` in ``parts``.
		* Load all mentions from ``mention_root``/``part`` for all ``part`` in ``parts``.
	"""

	def __init__(self, article_root, mention_root, parts=['']):
		self.__article_set               = ArticleSet(article_root, parts=parts)
		self.__id_to_article             = Id2Article(self.__article_set)

		self.__mention_bundle_set        = MentionBundleSet(article_root, mention_root, self.__article_set)
		self.__mention_set               = MentionSet(self.__mention_bundle_set)
		self.__id_to_mention             = Id2Mention(self.__mention_set)
		self.__article_to_mention_bundle = Article2MentionBundle(self.__mention_bundle_set)
		self.__id_to_mention_bundle      = Id2MentionBundle(self.__article_to_mention_bundle, self.__id_to_article)
		self.__head_to_mention_list      = Head2MentionList(self.__mention_set)

	@property
	def article_set(self):
		""":class:`.ArticleSet`: the article set."""
		return self.__article_set

	@property
	def id_to_article(self):
		""":class:`.Id2Article`: the dictionary maps article ID to article object."""
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
	def id_to_mention(self):
		""":class:`.Id2Mention`: the dictionary maps article ID, sentence ID, and mention ID to mention object."""
		return self.__id_to_mention

	@property
	def article_to_mention_bundle(self):
		""":class:`.Article2MentionBundle`: the dictionary maps article object to mention bundle."""
		return self.__article_to_mention_bundle

	@property
	def id_to_mention_bundle(self):
		""":class:`.Id2MentionBundle`: the dictionary maps article ID to mention bundle."""
		return self.__id_to_mention_bundle

	@property
	def head_to_mention_list(self):
		""":class:`.NameHead2MentionList`: the dictionary maps head word to mention object list."""
		return self.__head_to_mention_list
