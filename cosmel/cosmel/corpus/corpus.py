#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


from cosmel.util import *
from cosmel.repo import *
from cosmel.corpus.article import *
from cosmel.corpus.parsed  import *
from cosmel.corpus.mention import *


class Corpus:
	"""The corpus class.

	Args:
		article_root (str):    the path to the folder containing word segmented article files.
		parsed_root (str):     the path to the folder containing parsed article files.
		mention_root (str):    the path to the folder containing mention files.
		parts (list):          the list of article/mention parts.
		skips (list):          the list of articles to be ignored.
		skip_file (str):       the file of list of articles to be ignored.

	Notes:
		* Load all articles       from ``article_root``/``part`` for all ``part`` in ``parts``.
		* Load all parsed article from ``parsed_root``/``part``  for all ``part`` in ``parts``.
		* Load all mentions       from ``mention_root``/``part`` for all ``part`` in ``parts``.
	"""

	def __init__(self, article_root, *args, parsed_root=None, mention_root=None, parts=[''], skips=[], skip_file=''):

		if len(args) != 0:
			print('Please use mention_root=<mention_root> instead of using it directly.')
			assert len(args) == 0

		if skip_file:
			with open(skip_file) as fin:
				skips += fin.read().strip().split('\n')

		self.__article_set          = ArticleSet(article_root, parts=parts, skips=skips)
		self.__id_to_article        = Id2Article(self.__article_set)

		if parsed_root:
			self.__parsed_article_set   = ParsedArticleSet(parsed_root, self.__article_set)
			self.__id_to_parsed_article = Id2ParsedArticle(self.__id_to_article)

		if mention_root:
			self.reload_mention(mention_root)

	def reload_mention(self, mention_root):
		self.__mention_bundle_set   = MentionBundleSet(mention_root, self.__article_set)
		self.__mention_set          = MentionSet(self.__mention_bundle_set)
		self.__id_to_mention        = Id2Mention(self.__mention_set)
		self.__id_to_mention_bundle = Id2MentionBundle(self.__id_to_article)
		self.__head_to_mention_list = Head2MentionList(self.__mention_set)

	@property
	def article_set(self):
		""":class:`.ArticleSet`: the article set."""
		return self.__article_set

	@property
	def id_to_article(self):
		""":class:`.Id2Article`: the dictionary maps article ID to article object."""
		return self.__id_to_article

	@property
	def parsed_article_set(self):
		""":class:`.ParsedArticleSet`: the parsed article set."""
		return self.__parsed_article_set

	@property
	def id_to_parsed_article(self):
		""":class:`.Id2ParsedArticle`: the dictionary maps article ID to parsed article object."""
		return self.__id_to_parsed_article

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
	def id_to_mention_bundle(self):
		""":class:`.Id2MentionBundle`: the dictionary maps article ID to mention bundle."""
		return self.__id_to_mention_bundle

	@property
	def head_to_mention_list(self):
		""":class:`.NameHead2MentionList`: the dictionary maps head word to mention object list."""
		return self.__head_to_mention_list
