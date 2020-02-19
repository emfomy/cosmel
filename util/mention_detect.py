#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <http://muyang.pro>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import os
import sys

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *


def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Detect Mention.')

	argparser.add_argument('-c', '--corpus', required=True,
			help='store corpus data in directory "<CORPUS>/"')
	argparser.add_argument('-t', '--thread', type=int, \
			help='use <THREAD> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	corpus_root = os.path.normpath(args.corpus)

	nth = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print(f'Use {nth} threads')

	if nth <= 1:
		submain(corpus_root)
	else:
		import multiprocessing
		jobs = [multiprocessing.Process(target=submain, args=(corpus_root, nth, thrank,)) for thrank in range(nth)]
		for p in jobs: p.start()
		for p in jobs: p.join()
		for p in jobs: assert p.exitcode == 0


def submain(corpus_root, nth=None, thrank=0):

	target       = f'purged_article'
	tmp_root     = f'data/tmp'
	article_root = f'{corpus_root}/article/{target}_role'
	mention_root = f'{corpus_root}/mention/{target}'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(article_root))
	if nth: parts = parts[thrank:len(parts):nth]
	if not parts: return

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
