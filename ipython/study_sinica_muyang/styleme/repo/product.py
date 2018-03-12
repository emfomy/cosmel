#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import warnings

import collections.abc

from styleme.util import *
from styleme.repo.brand import *


class Product:
	"""The product object.

	Args:
		pid (str):              the ID.
		brand (:class:`.Brand`): the brand.
		name (str):              the name.
		head (str):              the head word.
		name_ws (str):           the segmented name.
		descr_ws (str):          the segmented description.
	"""

	def __init__(self, pid, brand, name, head, name_ws, descr_ws):
		self.__pid        = pid
		self.__brand       = brand
		self.__name        = name
		self.__head        = head
		self.__name_ws     = WsWords(name_ws)
		self.__descr_ws    = WsWords(descr_ws)
		self.__head_idx    = self.name_ws.txts.index(head)

	def __str__(self):
		return f'{self.__pid} {self.__brand!s} {self.__name}'

	def __repr__(self):
		return f'{self.__pid} {self.__brand!r} {self.__name_ws}'

	def __hash__(self):
		return hash(self.pid)

	@property
	def brand(self):
		""":class:`.Brand`: the brand."""
		return self.__brand

	@property
	def pid(self):
		"""str: the ID."""
		return self.__pid

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

	* Item: the product object (:class:`.Product`).

	Args:
		repo_root (str): the path to the folder containing data files.
		bname_to_brand (:class:`.BName2Brand`): the dictionary maps brand name to brand object.
	"""

	def __init__(self, repo_root, bname_to_brand):
		super().__init__()
		self.__data = list()

		tag_dict = {}
		with open(repo_root+'/product.lex') as fin_lex, open(repo_root+'/product.tag') as fin_tag:
			for line_lex, line_tag in zip(fin_lex, fin_tag):
				line_lex = line_lex.strip()
				line_tag = line_tag.strip()
				assert not line_lex == ''
				assert not line_tag == ''
				tag_dict[line_lex.split('\t')[0]] = line_tag

		descr_dict = {}
		with open(repo_root+'/product.descr') as fin_descr, open(repo_root+'/product.descr.tag') as fin_tag:
			for line_descr, line_tag in zip(fin_descr, fin_tag):
				line_descr = line_descr.strip()
				line_tag = line_tag.strip()
				assert not line_descr == ''
				assert not line_tag == ''
				descr_dict[line_descr.split('\t')[0]] = line_tag

		head_dict = {}
		with open(repo_root+'/product.head') as fin_head:
			for line in fin_head:
				line = line.strip()
				assert not line == ''
				pid, head = line.split('\t')
				head_dict[pid] = head

		with open(repo_root+'/product.txt') as fin_txt:
			for line in fin_txt:
				line = line.strip()
				assert not line == ''
				pid, bname, name = line.split('\t')
				descr_ws = descr_dict.get(pid, '')
				self.__data.append(Product(pid, bname_to_brand[bname], name, head_dict[pid], tag_dict[name], descr_ws))

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
	* Item: the product object (:class:`.Product`).

	Args:
		product_set (:class:`.ProductSet`): the product set.
	"""

	def __init__(self, product_set):
		super().__init__()
		self.__data = dict()
		for product in product_set:
			assert product.pid not in self.__data
			self.__data[product.pid] = product

	def __contains__(self, key):
		return key in self.__data

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)


class BrandPName2Product(collections.abc.Mapping):
	"""The dictionary maps brand object and product name to product object.

	* Key:  the tuple of brand object (:class:`.Brand`) and product name (str).
	* Item: the product object (:class:`.Product`).

	Args:
		product_set (:class:`.ProductSet`): the product set.
	"""

	def __init__(self, product_set):
		super().__init__()
		self.__data = dict()
		for product in product_set:
			pair = (product.brand, product.name,)
			assert pair not in self.__data
			self.__data[pair] = product

	def __contains__(self, key):
		return self.__keytransform__(key) in self.__data

	def __getitem__(self, key):
		return self.__data[self.__keytransform__(key)]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def __keytransform__(self, key):
		return (key[0], prune_string(key[1]),)


class BNamePName2Product(collections.abc.Sequence):
	"""The dictionary maps brand name and product name to product.

	* Key:  the tuple of brand name (str) and product name (str).
	* Item: the product object (:class:`.Product`).

	Args:
		brand_pname_to_product (:class:`.BrandPName2Product`): the dictionary maps brand object and product name to product object.
		bname_to_brand         (:class:`.BName2Brand`):        the dictionary maps name and brand.
	"""

	def __init__(self, brand_pname_to_product, bname_to_brand):
		super().__init__()
		self.__data = brand_pname_to_product
		self.__key  = bname_to_brand

	def __contains__(self, key):
		return self.__keytransform__(key) in self.__data

	def __getitem__(self, key):
		return self.__data[self.__keytransform__(key)]

	def __iter__(self):
		return iter(self.__data.values())

	def __len__(self):
		return len(self.__data)

	def __keytransform__(self, key):
		return (self.__key[key[0]], prune_string(key[1]),)


class PName2ProductList(collections.abc.Mapping):
	"""The dictionary maps product name to product object list.

	* Key:  the product name (str).
	* Item: :class:`.ReadOnlyList` of product object (:class:`.Product`).

	Args:
		product_set (:class:`.ProductSet`): the product set.
	"""

	def __init__(self, product_set):
		super().__init__()
		self.__data = dict()

		data_dict     = dict()
		for product in product_set:
			pair = (product.brand, product.head,)

			if product.name not in data_dict:
				data_dict[product.name] = [product]
			else:
				data_dict[product.name] += [product]

		for name, product_set in data_dict.items():
			self.__data[name] = ReadOnlyList(product_set)

	def __contains__(self, key):
		return self.__keytransform__(key) in self.__data

	def __getitem__(self, key):
		return self.__data[self.__keytransform__(key)]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def __keytransform__(self, key):
		return prune_string(key)


class BrandHead2ProductList(collections.abc.Mapping):
	"""The dictionary maps brand object and head word to product object list.

	* Key:  tuple of brand object (:class:`.Brand`) and product head word (str).
	* Item: :class:`.ReadOnlyList` of product object (:class:`.Product`).

	Args:
		product_set (:class:`.ProductSet`): the product set.
	"""

	def __init__(self, product_set):
		super().__init__()
		self.__data     = dict()
		self.__by_brand = dict()
		self.__by_head  = dict()

		data_dict     = dict()
		by_brand_dict = dict()
		by_head_dict  = dict()
		for product in product_set:
			pair = (product.brand, product.head,)

			if pair not in data_dict:
				data_dict[pair] = [product]
			else:
				data_dict[pair] += [product]

			if product.brand not in by_brand_dict:
				by_brand_dict[product.brand] = [product]
			else:
				by_brand_dict[product.brand] += [product]

			if product.head not in by_head_dict:
				by_head_dict[product.head] = [product]
			else:
				by_head_dict[product.head] += [product]

		for pair, product_set in data_dict.items():
			self.__data[pair] = ReadOnlyList(product_set)
		for brand, product_set in by_brand_dict.items():
			self.__by_brand[brand] = ReadOnlyList(product_set)
		for head, product_set in by_head_dict.items():
			self.__by_head[head] = ReadOnlyList(product_set)

		self.__empty_collection = ReadOnlyList()

	def __contains__(self, key):
		if key[1] == slice(None):
			return key[0] in self.__by_brand
		else:
			return key in self.__data

	def __getitem__(self, key):
		assert key[0] != slice(None) or key[1] != slice(None)
		if key[0] == slice(None):
			return self.__by_head.get(key[1], self.__empty_collection)
		if key[1] == slice(None):
			return self.__by_brand.get(key[0], self.__empty_collection)
		return self.__data.get(key, self.__empty_collection)

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)


class BNameHead2ProductList(collections.abc.Sequence):
	"""The dictionary maps brand name and head word to product object list.

	* Key:  tuple of brand name (str) and product head word (str).
	* Item: :class:`.ReadOnlyList` of product object (:class:`.Product`).

	Args:
		brand_head_to_product_list (:class:`.BrandHead2Productlist`):
			the dictionary maps brand object and head word to product object list.
		bname_to_brand              (:class:`.BName2Brand`):
			the dictionary maps name and brand.
	"""

	def __init__(self, brand_head_to_product_list, bname_to_brand):
		super().__init__()
		self.__data = brand_head_to_product_list
		self.__key  = bname_to_brand

	def __contains__(self, key):
		return self.__keytransform__(key) in self.__data

	def __getitem__(self, key):
		return self.__data[self.__keytransform__(key)]

	def __iter__(self):
		return iter(self.__data.values())

	def __len__(self):
		return len(self.__data)

	def __keytransform__(self, key):
		return (self.__key[key[0]] if key[0] != slice(None) else slice(None), key[1],)
