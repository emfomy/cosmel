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
			chars (str): the text with tag. (the format should be several 'text(post-tag)'s seperated by <U+3000>s.)
	"""

	def __init__(self, chars):
		chars_seg = [seg for seg in chars.strip().split('　') if not seg == '']
		self.__txts = ReadOnlyList(w.split('(', 1)[0] for w in chars_seg)
		self.__tags = ReadOnlyList(w.split('(', 1)[1][:-1] for w in chars_seg)

	def __getitem__(self, idxs):
		retval = WsWords('')
		retval.__txts = self.__txts[idxs]
		retval.__tags = self.__tags[idxs]
		return retval

	def __len__(self):
		return len(self.__txts)

	def __str__(self):
		return '　'.join(['{}({})'.format(w, p) for w, p in zip(self.__txts, self.__tags)])

	def __repr__(self):
		return str(self)

	def __txtstr__(self):
		return ''.join(self.__txts)

	@property
	def txts(self):
		"""list -- the txts."""
		return self.__txts

	@property
	def tags(self):
		"""list -- the post-tags."""
		return self.__tags

def txtstr(obj):
	return obj.__txtstr__()
