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


class Product:
	"""The product class.

	Args:
		p_id (str):              the ID.
		brand (:class:`.Brand`): the brand.
		name (str):              the name.
		head (str):              the head word.
		name_ws (str):           the segmented name.
	"""

	def __init__(self, p_id, brand, name, head, name_ws):
		self.__p_id     = p_id
		self.__brand    = brand
		self.__name     = name
		self.__head     = head
		self.__name_ws  = WsWords(name_ws)
		self.__head_idx = self.name_ws.txts.index(head)

	def __str__(self):
		return '{} {} {}'.format(self.__p_id, self.__brand[-1], self.__name)

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
		"""str --- the head word."""
		return self.__head

	@property
	def name_ws(self):
		""":class:`.WsWords` --- the word-segmented name."""
		return self.__name_ws

	@property
	def descri_ws(self):
		""":class:`.WsWords` --- the word-segmented descritions."""
		return self.__name_ws[:self.__head_idx]

	@property
	def suffix_ws(self):
		""":class:`.WsWords` --- the word-segmented suffixes."""
		return self.__name_ws[self.__head_idx+1:]


class ProductSet(collections.abc.Collection):
	"""The set of products.

	* Item: product class (:class:`.Product`).

	Args:
		repo_path (str): the path to the folder containing data files.
		name2brand (:class:`.Name2Brand`): the dictionary maps name to brand.
	"""

	def __init__(self, repo_path, name2brand):
		super().__init__()
		self.__data = list()

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
				self.__data.append(Product(p_id, name2brand[b_name], name, head_dict[p_id], tag_dict[name]))

	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def __str__(self):
		return '\n'.join(map(str, self.__data))


class Id2Product(collections.abc.Mapping):
	"""The dictionary maps ID to product.

	* Key:  product ID.   (str).
	* Item: product class (:class:`.Product`).

	Args:
		products (:class:`.ProductSet`): the product set.
	"""

	def __init__(self, products):
		super().__init__()
		self.__data = dict()
		for product in products:
			assert product.p_id not in self.__data
			self.__data[product.p_id] = product

	def __contains__(self, item):
		return item in self.__data

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)


class BrandName2Product(collections.abc.Mapping):
	"""The dictionary maps brand and name to product.

	* Key:  tuple of brand class (:class:`.Brand`) and product name (str).
	* Item: product class (:class:`.Product`).

	Args:
		products (:class:`.ProductSet`): the product set.
	"""

	def __init__(self, products):
		super().__init__()
		self.__data = dict()
		for product in products:
			pair = (product.brand, product.name)
			assert pair not in self.__data
			self.__data[pair] = product

	def __contains__(self, item):
		return item in self.__data

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)


class BrandHead2Products(collections.abc.Mapping):
	"""The dictionary maps brand and head to product list.

	* Key:  tuple of brand class (:class:`.Brand`) and product head (str).
	* Item: :class:`.ReadOnlyList` of product class (:class:`.Product`).

	Args:
		products (:class:`.ProductSet`): the product set.
	"""

	def __init__(self, products):
		super().__init__()
		self.__data = dict()

		product_dict = dict()
		for product in products:
			pair = (product.brand, product.head)
			if pair not in product_dict:
				product_dict[pair] = [product]
			else:
				product_dict[pair] += [product]

		for pair, products in product_dict.items():
			self.__data[pair] = ReadOnlyList(products)

		self.__empty_collection = ReadOnlyList()

	def __contains__(self, item):
		return item in self.__data

	def __getitem__(self, key):
		return self.__data.get(key, self.__empty_collection)

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)
