#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import collections.abc
import itertools
import multiprocessing
import os

from styleme.util import *
from styleme.corpus.article import *


class Mention:
	"""The mention class.

	Args:
		article.   (:class:`.Article`):    the article containing this mention.
		s_id       (int):                  the line index in the aritcle.
		begin_idx  (int):                  the beginning index in the sentence.
		end_idx    (int):                  the ending index in the sentence.
		name2brand (:class:`.Name2Brand`): the dictionary maps name to brand.
		p_id       (str):                  the product ID.
	"""

	def __init__(self, name2brand, article, s_id, begin_idx, end_idx, p_id='', g_id=''):
		super().__init__()

		self.__article   = article
		self.__s_id      = int(s_id)
		self.__begin_idx = int(begin_idx)
		self.__end_idx   = int(end_idx)
		self.__p_id      = p_id
		self.__g_id      = g_id
		self.__brand     = name2brand[self.b_name]

	def __str__(self):
		return str(self.mention)

	def __repr__(self):
		return str(self)

	def __txtstr__(self):
		return txtstr(self.mention)

	@property
	def article(self):
		""":class:`.Article` --- the article containing this mention."""
		return self.__article

	@property
	def sentence(self):
		""":class:`.WsWords` --- the sentence containing this mention."""
		return self.__article[self.__s_id]

	@property
	def mention(self):
		""":class:`.WsWords` --- this mention."""
		return self.sentence[self.__begin_idx:self.__end_idx]

	@property
	def a_id(self):
		"""str --- the article ID."""
		return self.__article.a_id

	@property
	def s_id(self):
		"""int --- the sentence ID (the line index in the article)."""
		return self.__s_id

	@property
	def begin_idx(self):
		"""int --- the beginning index in the sentence."""
		return self.__begin_idx

	@property
	def end_idx(self):
		"""int --- the ending index in the sentence."""
		return self.__end_idx

	@property
	def p_id(self):
		"""int --- the product ID."""
		return self.__p_id

	@property
	def g_id(self):
		"""int --- the golden product ID."""
		return self.__g_id

	@property
	def brand(self):
		""":class:`.Brand` --- the brand."""
		return self.__brand

	@property
	def b_name(self):
		"""str --- the brand name."""
		return self.sentence.txts[self.__begin_idx]

	@property
	def head(self):
		"""str --- the head word."""
		return self.sentence.txts[self.__end_idx-1]


class MentionSet(collections.abc.Collection):
	"""The set of mentions.

	* Item: mention (:class:`.Mention`)

	Args:
		article_path (str):              the path to the folder containing word segmented article files.
		mention_path (str):              the path to the folder containing mention files.
		articles (:class:`.ArticleSet`): the set of articles.
		repo     (:class:`.Repo`):       the product repository class.
	"""

	def __init__(self, article_path, mention_path, articles, repo):
		super().__init__()
		with multiprocessing.Pool() as pool:
			results = [pool.apply_async(self._grep_mention, args=(article, article_path, mention_path, repo.name2brand,)) \
					for article in articles]
			self.__data = list(itertools.chain.from_iterable(result.get() for result in results))
		print()

	@classmethod
	def _grep_mention(self, article, article_path, mention_path, name2brand):
		mention_file = article.path.replace(article_path, mention_path)+'.mention'
		printr('Reading {}'.format(mention_file))
		with open(mention_file) as fin:
			mentions = [Mention(name2brand, article, *tuple(line.strip().split('\t'))) for line in fin]
		return mentions

	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)
