#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import collections.abc

from styleme.util.core import *


class WsWords(collections.abc.Sequence):
	"""The sequence of words.

		Args:
			chars (str): the text with tag.
	"""

	def __init__(self, chars):
		texts = []
		posts = []
		for w in chars.strip().strip('□').split('　'):
			w = w.split('(')
			texts.append('('.join(w[0:-1]))
			posts.append(w[-1].split(')')[0])

		self.__texts = ReadOnlyList(texts)
		self.__posts = ReadOnlyList(posts)

	def __getitem__(self, idxs):
		retval = WsWords('')
		retval.__texts = self.__texts[idxs]
		retval.__posts = self.__posts[idxs]
		return retval

	def __len__(self):
		return len(self.__texts)

	def __str__(self):
		return '　'.join(['{}({})'.format(w, p) for w, p in zip(self.__texts, self.__posts)])

	def __repr__(self):
		return str(self)

	def __textstr__(self):
		return ''.join(self.__texts)

	@property
	def texts(self):
		"""list -- the texts."""
		return self.__texts

	@property
	def posts(self):
		"""list -- the post-tags."""
		return self.__posts

def textstr(obj):
	return obj.__textstr__()
