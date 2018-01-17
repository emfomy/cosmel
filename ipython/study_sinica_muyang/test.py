#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

from styleme import *

if __name__ == '__main__':
	target        = '/prune_article_ws/part-00000'
	repo_path     = 'data/repo'
	article_path  = 'data/article'+target
	mention_path  = 'data/mention'+target

	repo = Repo(repo_path)
	corpus = Corpus(article_path, mention_path, repo)

	for key, mention_list in corpus.brandhead2mentions.items():
		print(key, [m.sentence for m in mention_list])

	# brands = list(repo.brands)
	# brands2 = list()

	# import pymp
	# with pymp.Parallel(4) as p:
	# 	for i in p.iterate(range(len(brands))):
	# 		with p.lock:
	# 			print(len(brands2))
	# 			brands2.append(brands[i])

	# print(len(brands2))

	# # for i in range(len(brands)):
	# # 	print(brands[i], brands2[i])

	pass
