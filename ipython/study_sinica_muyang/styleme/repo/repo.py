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

		self.__brand_set                  = BrandSet(repo_root)
		self.__bname_to_brand             = BName2Brand(self.__brand_set)

		self.__product_set                = ProductSet(repo_root, self.__bname_to_brand)
		self.__id_to_product              = Id2Product(self.__product_set)
		self.__brand_pname_to_product     = BrandPName2Product(self.__product_set)
		self.__bname_pname_to_product     = BNamePName2Product(self.__brand_pname_to_product, self.__bname_to_brand)

		self.__pname_to_product_list      = PName2ProductList(self.__product_set)
		self.__brand_head_to_product_list = BrandHead2ProductList(self.__product_set)
		self.__bname_head_to_product_list = BNameHead2ProductList(self.__brand_head_to_product_list, self.__bname_to_brand)

		self.__path = repo_root

	@property
	def infix_set(self):
		""":class:`.HeadSet`: the infix word set."""
		return self.__infix_set

	@property
	def head_set(self):
		""":class:`.InfixSet`: the head word set."""
		return self.__head_set

	@property
	def brand_set(self):
		""":class:`.BrandSet`: the brand set."""
		return self.__brand_set

	@property
	def bname_to_brand(self):
		""":class:`.BName2Brand`: the dictionary maps brand name to brand object."""
		return self.__bname_to_brand

	@property
	def product_set(self):
		""":class:`.ProductSet`: the product set."""
		return self.__product_set

	@property
	def id_to_product(self):
		""":class:`.Id2Product`: the dictionary maps ID to product."""
		return self.__id_to_product

	@property
	def brand_pname_to_product(self):
		""":class:`.BrandPName2Product`: the dictionary maps brand object and product name to product object."""
		return self.__brand_pname_to_product

	@property
	def bname_pname_to_product(self):
		""":class:`.BrandPName2Product`: the dictionary maps brand name and product name to product object."""
		return self.__bname_pname_to_product

	@property
	def pname_to_product_list(self):
		""":class:`.PName2ProductList`: the dictionary maps product name to product object list."""
		return self.__pname_to_product_list

	@property
	def brand_head_to_product_list(self):
		""":class:`.BrandHead2ProductList`: the dictionary maps brand object and head word to product object list."""
		return self.__brand_head_to_product_list

	@property
	def bname_head_to_product_list(self):
		""":class:`.BNameHead2ProductList`: the dictionary maps brand name and head word to product object list."""
		return self.__bname_head_to_product_list

	@property
	def path(self):
		"""str: the root path of the repo."""
		return self.__path
