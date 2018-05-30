#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import os
import sys

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from styleme import *


def indices(lst, ele, start=0, end=None):
	return [i+start for i, val in enumerate(lst[start:end]) if val == ele]


if __name__ == '__main__':

	assert len(sys.argv) > 1
	ver = sys.argv[1]

	target       = f'pruned_article'
	tmp_root     = f'data/tmp'
	data_root    = f'data/{ver}'
	article_root = f'{data_root}/article/{target}_role'
	mention_root = f'{data_root}/mention/{target}'
	repo_root    = f'{data_root}/repo'
	parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) > 2: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	articles = ArticleSet(article_root, parts=parts)

	max_len_mention = 10

	empty_file = tmp_root+'/empty.tmp'
	with open(empty_file, 'w'): pass

	# Grep mentions
	n = str(len(articles))
	for i, article in enumerate(articles):
		mention_file = transform_path(article.path, article_root, mention_root, '.json')
		printr(f'{i+1:0{len(n)}}/{n}\t{mention_file}')
		bundle = MentionBundle(empty_file, article)
		bundle._MentionBundle__data = [Mention(article, sid, mid) \
				for sid, line in enumerate(article) for mid in indices(line.roles, 'Head')]
		bundle.save(mention_file)
	print()

	pass
