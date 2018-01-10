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
	"""Product repositary class.

	Args:
		repo_path (str): the path to the folder containing data files.
	"""

	def __init__(self, repo_path):
		self.__brands     = BrandSet(repo_path)
		self.__name2brand = Name2Brand(self.brands)

		self.__products   = ProductSet(repo_path, self.name2brand)

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