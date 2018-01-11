#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import collections.abc

from styleme.util.core import *


class Word:
	"""The word class.

		Args:
			chars (str): the text with tag.
	"""

	def __init__(self, chars):
		chars = chars.split('(')
		self.__text = '('.join(chars[0:-1])
		self.__post = chars[-1][0:-1]

	def __str__(self):
		return '{}({})'.format(self.text, self.post)

	def __repr__(self):
		return str(self)

	@property
	def text(self):
		"""str -- the text."""
		return self.__text

	@property
	def post(self):
		"""str -- the post-tag."""
		return self.__post


class Sentence(collections.abc.Sequence):
	"""The sentence class.

		Args:
			chars (str): the text with tag.
	"""

	def __init__(self, chars):
		self.__texts = []
		self.__posts = []
		for w in chars.strip().strip('□').split('　'):
			w = w.split('(')
			self.__texts.append('('.join(w[0:-1]))
			self.__posts.append(w[-1][0:-1])

	def __getitem__(self, idxs):
		retval = Sentence('')
		retval.__texts = self.__texts[idxs]
		retval.__posts = self.__posts[idxs]
		return retval

	def __len__(self):
		return len(self.__texts)

	def __str__(self):
		return '　'.join(['{}({})'.format(w, p) for w, p in zip(self.__texts, self.__posts)])

	def __repr__(self):
		return str(self)

	@property
	def texts(self):
		"""list -- the texts."""
		return self.__texts

	@property
	def posts(self):
		"""list -- the post-tags."""
		return self.__posts

	@property
	def text_str(self):
		"""str -- the string view of the texts (without post-tags)."""
		return ''.join(self.__texts)

	def word(self, idx):
		""":class:`.Word` -- Get word at given position.

		Args:
			idx (range): the index range.
		"""
		return Word('{}({})'.format(self.__texts[idx], self.__posts[idx]))
