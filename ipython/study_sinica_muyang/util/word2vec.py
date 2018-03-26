#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import os
import sys

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

if __name__ == '__main__':

	assert len(sys.argv) > 1
	ver = sys.argv[1]

	data_root    = f'data/{ver}'
	target       = f'pruned_article'
	article_root = f'{data_root}/article/{target}_role'
	txt_file     = f'{data_root}/embedding/{target}.txt'

	# Concatenate articles
	os.makedirs(os.path.dirname(txt_file), exist_ok=True)
	with open(txt_file, 'w') as fout:
		articles = ArticleSet(article_root)
		n = str(len(articles))
		for i, article in enumerate(articles):
			printr(f'{i+1:0{len(n)}}/{n}\tProcessing {article.path}')
			for sentence in article:
				fout.write(' '.join(sentence.txts)+'\n')
	print()

	pass
