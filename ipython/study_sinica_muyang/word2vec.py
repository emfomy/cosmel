#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

from styleme import *


if __name__ == '__main__':

	target       = '/prune_article_ws'
	article_path = 'data/article'+target
	txt_file     = 'data/embedding'+target+'.txt'
	emb_file     = 'data/embedding'+target+'.dim300.emb.bin'

	# Concatenate articles
	articles = ArticleSet(article_path)
	os.makedirs(os.path.dirname(txt_file), exist_ok=True)
	with open(output_file, 'w') as fout:
		for article in articles:
			printr(f'Processing {article.path}')
			for sentence in article:
				fout.write(' '.join(sentence.txts)+'\n')

	pass
