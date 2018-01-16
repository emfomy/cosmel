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

	for mention in corpus.mentions:
		print(mention.a_id, mention.s_id, mention)

	pass
