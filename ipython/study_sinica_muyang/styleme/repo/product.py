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
		descr_ws (str):          the segmented description.
	"""

	def __init__(self, p_id, brand, name, head, name_ws, descr_ws):
		self.__p_id        = p_id
		self.__brand       = brand
		self.__name        = name
		self.__head        = head
		self.__name_ws     = WsWords(name_ws)
		self.__descr_ws    = WsWords(descr_ws)
		self.__head_idx    = self.name_ws.txts.index(head)

	def __str__(self):
		return f'{self.__p_id} {self.__brand!s} {self.__name}'

	def __repr__(self):
		return f'{self.__p_id} {self.__brand!r} {self.__name_ws}'

	@property
	def brand(self):
		""":class:`.Brand`: the brand."""
		return self.__brand

	@property
	def p_id(self):
		"""str: the ID."""
		return self.__p_id

	@property
	def name(self):
		"""str: the name (excluding brand)."""
		return self.__name

	@property
	def descr(self):
		"""str: the description."""
		return txtstr(self.__descr_ws)

	@property
	def head(self):
		"""str: the head word."""
		return self.__head

	@property
	def name_ws(self):
		""":class:`.WsWords`: the word-segmented name."""
		return self.__name_ws

	@property
	def descr_ws(self):
		""":class:`.WsWords`: the word-segmented description."""
		return self.__descr_ws

	@property
	def infix_ws(self):
		""":class:`.WsWords`: the word-segmented infix."""
		return self.__name_ws[:self.__head_idx]

	@property
	def suffix_ws(self):
		""":class:`.WsWords`: the word-segmented suffix."""
		return self.__name_ws[self.__head_idx+1:]


class ProductSet(collections.abc.Collection):
	"""The set of products.

	* Item: the product class (:class:`.Product`).

	Args:
		repo_root (str): the path to the folder containing data files.
		name_to_brand (:class:`.Name2Brand`): the dictionary maps brand name to brand object.
	"""

	def __init__(self, repo_root, name_to_brand):
		super().__init__()
		self.__data = list()

		tag_dict = {}
		with open(repo_root+'/products.lex') as fin_lex, open(repo_root+'/products.tag') as fin_tag:
			for line_lex, line_tag in zip(fin_lex, fin_tag):
				line_lex = line_lex.strip()
				line_tag = line_tag.strip()
				assert not line_lex == ''
				assert not line_tag == ''
				tag_dict[line_lex.split('\t')[0]] = line_tag

		descr_dict = {}
		with open(repo_root+'/products.descr') as fin_descr, open(repo_root+'/products.descr.tag') as fin_tag:
			for line_descr, line_tag in zip(fin_descr, fin_tag):
				line_descr = line_descr.strip()
				line_tag = line_tag.strip()
				assert not line_descr == ''
				assert not line_tag == ''
				descr_dict[line_descr.split('\t')[0]] = line_tag

		head_dict = {}
		with open(repo_root+'/products.head') as fin_head:
			for line in fin_head:
				line = line.strip()
				assert not line == ''
				p_id, head = line.split('\t')
				head_dict[p_id] = head

		with open(repo_root+'/products.txt') as fin_txt:
			for line in fin_txt:
				line = line.strip()
				assert not line == ''
				p_id, b_name, name = line.split('\t')
				descr_ws = descr_dict.get(p_id, '')
				self.__data.append(Product(p_id, name_to_brand[b_name], name, head_dict[p_id], tag_dict[name], descr_ws))

	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def __str__(self):
		return '\n'.join(map(str, self.__data))

	def __repr__(self):
		return '\n'.join(map(repr, self.__data))


class Id2Product(collections.abc.Mapping):
	"""The dictionary maps ID to product.

	* Key:  the product ID.   (str).
	* Item: the product class (:class:`.Product`).

	Args:
		product_set (:class:`.ProductSet`): the product set.
	"""

	def __init__(self, product_set):
		super().__init__()
		self.__data = dict()
		for product in product_set:
			assert product.p_id not in self.__data
			self.__data[product.p_id] = product

	def __contains__(self, key):
		return key in self.__data

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)


class BrandName2Product(collections.abc.Mapping):
	"""The dictionary maps brand object and product name to product object.

	* Key:  the tuple of brand class (:class:`.Brand`) and product name (str).
	* Item: the product class (:class:`.Product`).

	Args:
		product_set (:class:`.ProductSet`): the product set.
	"""

	def __init__(self, product_set):
		super().__init__()
		self.__data = dict()
		for product in product_set:
			pair = (product.brand, product.name)
			assert pair not in self.__data
			self.__data[pair] = product

	def __contains__(self, key):
		return key in self.__data

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)


class NameName2Product(collections.abc.Sequence):
	"""The dictionary maps brand name and product name to product.

	* Key:  the tuple of brand name (str) and product name (str).
	* Item: the product class (:class:`.Product`).

	Args:
		brand_name_to_product (:class:`.BrandName2Product`): the dictionary maps brand object and product name to product object.
		name_to_brand         (:class:`.Name2Brand`):        the dictionary maps name and brand.
	"""

	def __init__(self, brand_name_to_product, name_to_brand):
		super().__init__()
		self.__data = brand_name_to_product
		self.__key  = name_to_brand

	def __contains__(self, key):
		return self.__key[key] in self.__data

	def __getitem__(self, key):
		return self.__data[self.__key[key]]

	def __iter__(self):
		return iter(self.__data.values())

	def __len__(self):
		return len(self.__data)


class BrandHead2ProductList(collections.abc.Mapping):
	"""The dictionary maps brand object and head word to product object list.

	* Key:  tuple of brand class (:class:`.Brand`) and product head (str).
	* Item: :class:`.ReadOnlyList` of product class (:class:`.Product`).

	Args:
		product_set (:class:`.ProductSet`): the product set.
	"""

	def __init__(self, product_set):
		super().__init__()
		self.__data = dict()

		product_dict = dict()
		for product in product_set:
			pair = (product.brand, product.head)
			if pair not in product_dict:
				product_dict[pair] = [product]
			else:
				product_dict[pair] += [product]

		for pair, product_set in product_dict.items():
			self.__data[pair] = ReadOnlyList(product_set)

		self.__empty_collection = ReadOnlyList()

	def __contains__(self, key):
		return key in self.__data

	def __getitem__(self, key):
		return self.__data.get(key, self.__empty_collection)

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)


class NameHead2ProductList(collections.abc.Sequence):
	"""The dictionary maps brand name and head word to product object list.

	* Key:  tuple of brand class (:class:`.Brand`) and product head (str).
	* Item: :class:`.ReadOnlyList` of product class (:class:`.Product`).

	Args:
		brand_head_to_product_list (:class:`.BrandHead2Productlist`):
			the dictionary maps brand object and head word to product object list.
		name_to_brand              (:class:`.Name2Brand`):
			the dictionary maps name and brand.
	"""

	def __init__(self, brand_head_to_product_list, name_to_brand):
		super().__init__()
		self.__data = brand_head_to_product_list
		self.__key  = name_to_brand

	def __contains__(self, key):
		return self.__key[key] in self.__data

	def __getitem__(self, key):
		return self.__data[self.__key[key[0]], key[1]]

	def __iter__(self):
		return iter(self.__data.values())

	def __len__(self):
		return len(self.__data)
