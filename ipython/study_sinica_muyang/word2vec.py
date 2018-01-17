#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

from styleme import *


if __name__ == '__main__':

	target        = '/prune_article_ws'
	article_path  = 'data/article'+target
	output_file   = 'data/embedding'+target+'.txt'

	articles = ArticleSet(article_path)

	os.makedirs(os.path.dirname(output_file), exist_ok=True)
	with open(output_file, 'w') as fout:
		for article in articles:
			printr('Processing {}'.format(article.path))
			for sentence in article:
				fout.write(' '.join(sentence.txts)+'\n')
	print()

	pass
