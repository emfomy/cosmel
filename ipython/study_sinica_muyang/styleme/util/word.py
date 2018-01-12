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
		chars_seg = chars.strip().strip('□').split('　')
		self.__texts = ReadOnlyList(w.split('(', 1)[0] for w in chars_seg)
		self.__posts = ReadOnlyList(w.split('(', 1)[1][:-1] for w in chars_seg)

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
