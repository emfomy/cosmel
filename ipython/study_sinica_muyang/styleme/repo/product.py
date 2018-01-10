#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import warnings

import collections.abc

from styleme.util import *
from styleme.repo.brand import *


class Product(collections.abc.Collection):
	"""The product details.

	Args:
		p_id (str):              the ID.
		brand (:class:`.Brand`): the brand.
		name (str):              the name.
		head (str):              the head.
		name_ws (str):           the segmented name.
	"""

	def __init__(self, p_id, brand, name, head, name_ws):
		super().__init__()
		self.__p_id     = p_id
		self.__brand    = brand
		self.__name     = name
		self.__head     = head
		self.__name_seg = Sentence(name_ws)
		self.__head_idx = self.name_seg.texts.index(head)

	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def __str__(self):
		return str(self.__data)

	def __repr__(self):
		return str(self)

	@property
	def brand(self):
		""":class:`.Brand` --- the brand."""
		return self.__brand

	@property
	def p_id(self):
		"""str --- the ID."""
		return self.__p_id

	@property
	def name(self):
		"""str --- the name."""
		return self.__name

	@property
	def head(self):
		"""str --- the head."""
		return self.__head

	@property
	def name_seg(self):
		""":class:`.Sentence` --- the name_seg."""
		return self.__name_seg

	@property
	def descri(self):
		""":class:`.Sentence` --- the descritions."""
		return self.__name_seg[:self.__head_idx]

	@property
	def suffix(self):
		""":class:`.Sentence` --- the suffixes."""
		return self.__name_seg[self.__head_idx+1:]


class ProductSet(collections.abc.Collection):
	"""The set of products.

	Args:
		repo_path (str): the path to the folder containing data files.
		name2brand (:class:`.Name2Brand`): the dictionary maps name to brand.
	"""

	def __init__(self, repo_path, name2brand):
		super().__init__()
		self.__data = set()

		tag_dict = {}
		with open(repo_path+'/products.lex') as fin_lex, open(repo_path+'/products.tag') as fin_tag:
			for line_lex, line_tag in zip(fin_lex, fin_tag):
				line_lex = line_lex.strip()
				line_tag = line_tag.strip()
				assert not line_lex == ''
				assert not line_tag == ''
				tag_dict[line_lex.split('\t')[0]] = line_tag

		head_dict = {}
		with open(repo_path+'/products.head') as fin_head:
			for line in fin_head:
				line = line.strip()
				assert not line == ''
				p_id, head = line.split('\t')
				head_dict[p_id] = head

		with open(repo_path+'/products.txt') as fin_txt:
			for line in fin_txt:
				line = line.strip()
				assert not line == ''
				p_id, b_name, name = line.split('\t')
				self.__data.add(Product(p_id, name2brand[b_name], name, head_dict[p_id], tag_dict[name]))

	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)
