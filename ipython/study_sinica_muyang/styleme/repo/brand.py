#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import collections.abc

from styleme.util import *


class Brand(collections.abc.Sequence):
	"""The brand class (contains list of brand aliases).

	Args:
		aliases (list): the brand aliases.
	"""

	def __init__(self, aliases):
		super().__init__()
		self.__data = sorted(aliases)

	def __contains__(self, item):
		return item in self.__data

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def __str__(self):
		return str(self.__data)

	def __repr__(self):
		return str(self)


class BrandSet(collections.abc.Collection):
	"""The set of brands.

	Args:
		repo_path (str): the path to the folder containing data files.
	"""

	def __init__(self, repo_path):
		super().__init__()
		self.__data = list()
		with open(repo_path+'/brands.txt') as fin:
			for line in fin:
				line = line.strip()
				assert not line == ''
				self.__data.append(Brand(line.split('\t')))

	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def __str__(self):
		return '\n'.join(map(str, self.__data))


class Name2Brand(collections.abc.Mapping):
	"""The dictionary maps name to brand.

	Args:
		brands (:class:`.BrandSet`): the brand set.
	"""

	def __init__(self, brands):
		super().__init__()
		self.__data = dict()
		for brand in brands:
			for b_name in brand:
				assert b_name not in self
				self.__data[b_name] = brand

	def __contains__(self, item):
		return item in self.__data

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)
