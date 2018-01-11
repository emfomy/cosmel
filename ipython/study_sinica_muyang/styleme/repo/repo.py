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
		self.__brands             = BrandSet(repo_path)
		self.__name2brand         = Name2Brand(self.__brands)

		self.__products           = ProductSet(repo_path, self.__name2brand)
		self.__id2product         = Id2Product(self.__products)
		self.__brandname2product  = BrandName2Product(self.__products)
		self.__brandhead2products = BrandHead2Products(self.__products)

	@property
	def brands(self):
		""":class:`.BrandSet` --- the brand set."""
		return self.__brands

	@property
	def name2brand(self):
		""":class:`.Name2Brand` --- the dictionary maps name to brand."""
		return self.__name2brand

	@property
	def products(self):
		""":class:`.ProductSet` --- the product set."""
		return self.__products

	@property
	def id2product(self):
		""":class:`.Id2Product` --- the dictionary maps ID to product."""
		return self.__id2product

	@property
	def brandname2product(self):
		""":class:`.Id2Product` --- the dictionary maps brand and name to product."""
		return self.__brandname2product

	@property
	def brandhead2products(self):
		""":class:`.Id2Product` --- the dictionary maps brand and head to product list."""
		return self.__brandhead2products
