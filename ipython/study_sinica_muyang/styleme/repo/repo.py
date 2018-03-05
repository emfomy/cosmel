#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


from styleme.util import *
from styleme.repo.word import *
from styleme.repo.brand import *
from styleme.repo.product import *


class Repo:
	"""The product repository class.

	Args:
		repo_root (str): the path to the folder containing data files.
	"""

	def __init__(self, repo_root):
		self.__head_set                   = HeadSet(repo_root)
		self.__infix_set                  = InfixSet(repo_root)
		self.__product_name_set           = ProductNameSet(repo_root)

		self.__brand_set                  = BrandSet(repo_root)
		self.__name_to_brand              = Name2Brand(self.__brand_set)

		self.__product_set                = ProductSet(repo_root, self.__name_to_brand)
		self.__id_to_product              = Id2Product(self.__product_set)
		self.__brand_name_to_product      = BrandName2Product(self.__product_set)
		self.__name_name_to_product       = NameName2Product(self.__brand_name_to_product, self.__name_to_brand)
		self.__brand_head_to_product_list = BrandHead2ProductList(self.__product_set)
		self.__name_head_to_product_list  = NameHead2ProductList(self.__brand_head_to_product_list, self.__name_to_brand)

	@property
	def infix_set(self):
		""":class:`.HeadSet`: the infix word set."""
		return self.__infix_set

	@property
	def head_set(self):
		""":class:`.InfixSet`: the head word set."""
		return self.__head_set

	@property
	def product_name_set(self):
		""":class:`.ProductNameSet`: the product name set."""
		return self.__product_name_set

	@property
	def brand_set(self):
		""":class:`.BrandSet`: the brand set."""
		return self.__brand_set

	@property
	def name_to_brand(self):
		""":class:`.Name2Brand`: the dictionary maps brand name to brand object."""
		return self.__name_to_brand

	@property
	def product_set(self):
		""":class:`.ProductSet`: the product set."""
		return self.__product_set

	@property
	def id_to_product(self):
		""":class:`.Id2Product`: the dictionary maps ID to product."""
		return self.__id_to_product

	@property
	def brand_name_to_product(self):
		""":class:`.BrandName2Product`: the dictionary maps brand object and product name to product object."""
		return self.__brand_name_to_product

	@property
	def name_name_to_product(self):
		""":class:`.BrandName2Product`: the dictionary maps brand name and product name to product."""
		return self.__name_name_to_product

	@property
	def brand_head_to_product_list(self):
		""":class:`.BrandHead2ProductList`: the dictionary maps brand object and head word to product object list."""
		return self.__brand_head_to_product_list

	@property
	def name_head_to_product_list(self):
		""":class:`.NameHead2ProductList`: the dictionary maps brand name and head word to product object list."""
		return self.__name_head_to_product_list
