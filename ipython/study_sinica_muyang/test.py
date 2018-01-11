#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

from styleme import *

if __name__ == '__main__':
	repo = Repo('data/repo')
	for brand in repo.brands:
		print(list(brand))
	# for product in repo.products:
	# 	print(product.suffix)

	pass
