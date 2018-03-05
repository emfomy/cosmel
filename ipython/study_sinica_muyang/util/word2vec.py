#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import os
import sys

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

if __name__ == '__main__':

	assert len(sys.argv) >= 2
	ver = sys.argv[1]

	data_root    = f'data/{ver}'
	target       = f'pruned_article_ws'
	article_root = f'{data_root}/article/{target}'
	txt_file     = f'{data_root}/embedding/{target}.txt'
	emb_file     = f'{data_root}/embedding/{target}.dim300.emb.bin'

	# Concatenate articles
	articles = ArticleSet(article_root)
	os.makedirs(os.path.dirname(txt_file), exist_ok=True)
	with open(txt_file, 'w') as fout:
		for article in articles:
			printr(f'Processing {article.path}')
			for sentence in article:
				fout.write(' '.join(sentence.txts)+'\n')
	print()

	pass
