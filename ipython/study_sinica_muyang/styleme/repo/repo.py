#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

from styleme.util import *
from styleme.repo.brand import *
from styleme.repo.product import *


class Repo:
	"""The product repository class.

	Args:
		repo_path (str): the path to the folder containing data files.
	"""

	def __init__(self, repo_path):
		self.__brand_set                 = BrandSet(repo_path)
		self.__name_to_brand             = Name2Brand(self.__brand_set)

		self.__product_set               = ProductSet(repo_path, self.__name_to_brand)
		self.__id_to_product             = Id2Product(self.__product_set)
		self.__brandname_to_product      = BrandName2Product(self.__product_set)
		self.__brandhead_to_product_list = BrandHead2ProductList(self.__product_set)

	@property
	def brands(self):
		""":class:`.BrandSet`: the brand set."""
		return self.__brand_set

	@property
	def name_to_brand(self):
		""":class:`.Name2Brand`: the dictionary maps name to brand."""
		return self.__name_to_brand

	@property
	def products(self):
		""":class:`.ProductSet`: the product set."""
		return self.__product_set

	@property
	def id_to_product(self):
		""":class:`.Id2Product`: the dictionary maps ID to product."""
		return self.__id_to_product

	@property
	def brandname_to_product(self):
		""":class:`.BrandName2Product`: the dictionary maps brand and name to product."""
		return self.__brandname_to_product

	@property
	def brandhead_to_product_list(self):
		""":class:`.BrandHead2ProductList`: the dictionary maps brand and head to product list."""
		return self.__brandhead_to_product_list
