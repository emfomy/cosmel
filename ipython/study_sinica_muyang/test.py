#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

from styleme import *

if __name__ == '__main__':
	repo = Repo('data/repo')
	corpus = Corpus('data/article/prune_article_ws/part-00000', repo)
	for _, a in corpus.id2article.items():
		print(a[0])

	pass
