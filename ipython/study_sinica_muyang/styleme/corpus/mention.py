#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import collections.abc
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

	def __init__(self, article, s_id, begin_idx, end_idx, name2brand, p_id=None):
		super().__init__()

		self.__article   = article
		self.__s_id      = int(s_id)
		self.__begin_idx = int(begin_idx)
		self.__end_idx   = int(end_idx)
		self.__p_id      = p_id
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
		articles (:class:`.ArticleSet`): the set of articles.
		repo     (:class:`.Repo`):       the product repository class.
	"""

	__max_len_mention = 10

	def __init__(self, articles, repo):
		super().__init__()

		self.__data = list()
		for article in articles:
			self.__data += self.__grep_mention(repo.name2brand, article)

		# with multiprocessing.Pool() as p:
		# 	self.__data = p.map(self.__grep_mention, articles)
		# print()

	@classmethod
	def __grep_mention(self, name2brand, article):
		mentions = list()
		for s_id, line in enumerate(article):
			idx = 0
			while idx < len(line):
				if line.tags[idx] == 'N_Brand':
					begin_idx = idx
					if 'N_Head' in line.tags[idx:idx+self.__max_len_mention]:
						idx = min(idx+self.__max_len_mention, len(line)-1)
						while idx > begin_idx:
							if line.tags[idx] == 'N_Head':
								mentions.append(Mention(article, s_id, begin_idx, idx+1, name2brand))
								break
							idx -= 1
				idx += 1
		return mentions


	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)
