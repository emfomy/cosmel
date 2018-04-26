#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import sys

from styleme import *

if __name__ == '__main__':

	# assert len(sys.argv) == 2
	# ver = sys.argv[1]

	# target       = f'pruned_article'
	# target_ver   = f'_gid_20180409'
	# data_root    = f'data/{ver}'
	# repo_root    = f'{data_root}/repo'
	# article_root = f'{data_root}/article/{target}_role'
	# mention_root = f'{data_root}/mention/{target}{target_ver}'
	# bad_article  = f'{data_root}/article/bad_article.txt'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	# if len(sys.argv) > 2: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	# with open(bad_article) as fin:
	# 	skip_list = fin.read().strip().split('\n')

	# repo   = Repo(repo_root)
	# corpus = Corpus(article_root, mention_root, parts=parts, skips=skip_list)

	print(sys.argv)

	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('--args', nargs='*')
	args = parser.parse_args()
	print(args)

	pass
