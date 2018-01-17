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
		brand_idx  (int):                  the brand index in the sentence.
		head_idx   (int):                  the head index in the sentence.
		name2brand (:class:`.Name2Brand`): the dictionary maps name to brand.
		p_id       (str):                  the product ID.
		g_id       (str):                  the golden product ID.
	"""

	def __init__(self, name2brand, article, s_id, brand_idx, head_idx, p_id='', g_id=''):
		super().__init__()

		self.__article   = article
		self.__s_id      = int(s_id)
		self.__brand_idx = int(brand_idx)
		self.__head_idx  = int(head_idx)
		self.__p_id      = p_id
		self.__g_id      = g_id
		self.__brand     = name2brand[self.b_name]

	def __str__(self):
		return str(self.mention)

	def __repr__(self):
		return repr(self.mention)

	def __txtstr__(self):
		return txtstr(self.mention)

	@property
	def article(self):
		""":class:`.Article`: the article containing this mention."""
		return self.__article

	@property
	def sentence(self):
		""":class:`.WsWords`: the sentence containing this mention."""
		return self.__article[self.__s_id]

	@property
	def mention(self):
		""":class:`.WsWords`: this mention."""
		return self.sentence[self.slice]

	@property
	def a_id(self):
		"""str: the article ID."""
		return self.__article.a_id

	@property
	def s_id(self):
		"""int: the sentence ID (the line index in the article)."""
		return self.__s_id

	@property
	def brand_idx(self):
		"""int: the brand index in the sentence."""
		return self.__brand_idx

	@property
	def head_idx(self):
		"""int: the head index in the sentence."""
		return self.__head_idx

	@property
	def beginning_idx(self):
		"""int: the beginning index in the sentence (= :attr:`brand_idx`)."""
		return self.__brand_idx

	@property
	def ending_idx(self):
		"""int: the ending index in the sentence (= :attr:`head_idx` +1)."""
		return self.__head_idx+1

	@property
	def slice(self):
		"""slice: the mention slice index in the sention (= :attr:`beginning_idx` : :attr:`ending_idx`)."""
		return slice(self.beginning_idx, self.ending_idx)

	@property
	def p_id(self):
		"""int: the product ID."""
		return self.__p_id

	@property
	def g_id(self):
		"""int: the golden product ID."""
		return self.__g_id

	@property
	def brand(self):
		""":class:`.Brand`: the brand."""
		return self.__brand

	@property
	def b_name(self):
		"""str: the brand name."""
		return self.sentence.txts[self.__brand_idx]

	@property
	def head(self):
		"""str: the head word."""
		return self.sentence.txts[self.__head_idx]


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
		# with multiprocessing.Pool() as pool:
		# 	results = [pool.apply_async(self._grep_mention, args=(article, article_path, mention_path, repo.name2brand,)) \
		# 			for article in articles]
		# 	self.__data = list(itertools.chain.from_iterable(result.get() for result in results))
		# 	del results
		results = [self._grep_mention(article, article_path, mention_path, repo.name2brand) \
				for article in articles]
		self.__data = list(itertools.chain.from_iterable(result for result in results))
		print()

	@staticmethod
	def _grep_mention(article, article_path, mention_path, name2brand):
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


class Path2Mentions(collections.abc.Mapping):
	"""The dictionary maps file path to mention list.

	* Key:  the related file path of the article (str).
	* Item: :class:`.ReadOnlyList` of mention class (:class:`.Mention`).

	Args:
		mentions (:class:`.MentionSet`): the mention set.
	"""

	def __init__(self, mentions):
		super().__init__()
		self.__data = dict()

		mention_dict = dict()
		for mention in mentions:
			path = mention.article.path
			if path not in mention_dict:
				mention_dict[path] = [mention]
			else:
				mention_dict[path] += [mention]

		for path, mentions in mention_dict.items():
			self.__data[path] = ReadOnlyList(mentions)

	def __contains__(self, item):
		return item in self.__data

	def __getitem__(self, key):
		return self.__data.get(key)

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)


class BrandHead2Mentions(collections.abc.Mapping):
	"""The dictionary maps brand and head to mention list.

	* Key:  tuple of brand class (:class:`.Brand`) and mention head (str).
	* Item: :class:`.ReadOnlyList` of mention class (:class:`.Mention`).

	Args:
		mentions (:class:`.MentionSet`): the mention set.
	"""

	def __init__(self, mentions):
		super().__init__()
		self.__data = dict()

		mention_dict = dict()
		for mention in mentions:
			pair = (mention.brand, mention.head)
			if pair not in mention_dict:
				mention_dict[pair] = [mention]
			else:
				mention_dict[pair] += [mention]

		for pair, mentions in mention_dict.items():
			self.__data[pair] = ReadOnlyList(mentions)

		self.__empty_collection = ReadOnlyList()

	def __contains__(self, item):
		return item in self.__data

	def __getitem__(self, key):
		return self.__data.get(key, self.__empty_collection)

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

