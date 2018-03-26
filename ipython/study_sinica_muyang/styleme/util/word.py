#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import collections.abc

from styleme.util.core import *


class WsWords(collections.abc.Sequence):
	"""The sequence of word-segmented words.

		Args:
			chars (str): the text with tag. (the format should be several 'text(post-tag)'s seperated by <U+3000>s.)
	"""

	@classmethod
	def __split(self, w):
		txt, w    = w.split('(', 1)
		tag, role = w.split(')', 1)
		return txt, tag, role

	def __init__(self, chars):
		chars_seg = [self.__split(w) for w in chars.strip().split('　') if not w == '']
		self.__txts  = [w[0] for w in chars_seg]
		self.__tags  = [w[1] for w in chars_seg]
		self.__roles = [w[2] for w in chars_seg]

	def index(self, word, *args):
		"""int -- returns the index of the first word.

			Args:
				word (tuple): the tuple of text and tag, (optional) and role.
		"""
		if isinstance(word, tuple):
			if len(word) == 2:
				return list(self.zip2).index(word, *args)
			if len(word) == 3:
				return list(self.zip3).index(word, *args)
		raise ValueError(f'{word} is not in list')

	def __contains__(self, key):
		return key in self.zip2 or key in self.zip3

	def __getitem__(self, idxs):
		retval = WsWords('')
		retval.__txts  = self.__txts[idxs]
		retval.__tags  = self.__tags[idxs]
		retval.__roles = self.__roles[idxs]
		return retval

	def __len__(self):
		return len(self.__txts)

	def __str__(self):
		return '　'.join([f'{txt}({tag})' for txt, tag in self.zip2])

	def __repr__(self):
		return str(self)

	def __txtstr__(self):
		return ''.join(self.__txts)

	def __roledstr__(self):
		return '　'.join([f'{txt}({tag}){role}' for txt, tag, role in self.zip3])

	def __roledtxtstr__(self):
		return ''.join([f'{txt}{role}' for txt, _, role in self.zip3])

	@property
	def txts(self):
		""":class:`list` -- the texts."""
		return self.__txts

	@property
	def tags(self):
		""":class:`list` -- the post-tags."""
		return self.__tags

	@property
	def roles(self):
		""":class:`list` -- the roles."""
		return self.__roles

	@property
	def zip(self):
		"""zip -- the zip iterator of the texts, the tags, and the roles. (= :attr:`zip3`)."""
		return zip(self.__txts, self.__tags, self.__roles)

	@property
	def zip2(self):
		"""zip -- the zip iterator of the texts and the tags."""
		return zip(self.__txts, self.__tags)

	@property
	def zip3(self):
		"""zip -- the zip iterator of the texts, the tags, and the roles.."""
		return zip(self.__txts, self.__tags, self.__roles)

def txtstr(obj):
	"""str -- return the string of texts (obj.txts)"""
	return obj.__txtstr__()

def roledstr(obj):
	"""str -- return the string with role (obj.txts, obj.tags, obj.roles)"""
	return obj.__roledstr__()

def roledtxtstr(obj):
	"""str -- return the string with texts and role (obj.txts, obj.roles)"""
	return obj.__roledtxtstr__()
