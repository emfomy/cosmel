#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import os
import sys

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *


def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Merge Mention.')

	argparser.add_argument('-v', '--ver', metavar='<ver>#<date>', required=True, \
			help='load repo from "data/<ver>", and load/save corpus data from/into "data/<ver>/corpus/<date>"')
	argparser.add_argument('-t', '--thread', metavar='<thread>', type=int, \
			help='use <thread> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	vers = args.ver.split('#')
	assert len(vers) == 2, argparser.format_usage()
	ver  = vers[0]
	date = vers[1]
	assert len(ver)  > 0
	assert len(date) > 0

	nth = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print(f'Use {nth} threads')

	import multiprocessing
	with multiprocessing.Pool(nth) as pool:
		results = [pool.apply_async(submain, args=(ver, date, nth, thrank,)) for thrank in range(nth)]
		[result.get() for result in results]
		del results


def submain(ver, date, nth=None, thrank=0):

	target       = f'purged_article'
	tmp_root     = f'data/tmp'
	data_root    = f'data/{ver}'
	corpus_root  = f'data/{ver}/corpus/{date}'
	repo_root    = f'{data_root}/repo'
	article_root = f'{corpus_root}/article/{target}_role'
	mention_root = f'{corpus_root}/mention/{target}'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(article_root))
	if nth: parts = parts[thrank:len(parts):nth]

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
	if not thrank: print()


def indices(lst, ele, start=0, end=None):
	return [i+start for i, val in enumerate(lst[start:end]) if val == ele]


if __name__ == '__main__':

	main()
	print()
	pass
