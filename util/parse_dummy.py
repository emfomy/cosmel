#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import itertools
import os
import re
import sys

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *
from parser import CKIPParser_Client as ckipparser


def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Parse Sentence (Dummy).')

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
		jobs = [multiprocessing.Process(target=submain, args=(corpus_root, nth, thrank)) for thrank in range(nth)]
		for p in jobs: p.start()
		for p in jobs: p.join()
		for p in jobs: assert p.exitcode == 0


def submain(corpus_root, nth=None, thrank=0):

	target       = f'purged_article'
	target_parse = f'parsed_article'
	ws_re2_root  = f'{corpus_root}/article/{target}_ws_re2'
	parse_root   = f'{corpus_root}/article/{target_parse}_parse'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(ws_re2_root))
	if nth: parts = parts[thrank:len(parts):nth]

	articles = ArticleSet(ws_re2_root, parts=parts)

	# Prune Articles
	n = str(len(articles))
	for i, article in enumerate(articles):
		parse_file = transform_path(article.path, ws_re2_root, parse_root, '.parse')
		os.makedirs(os.path.dirname(parse_file), exist_ok=True)
		printr(f'{i+1:0{len(n)}}/{n}\t{parse_file}')
		with open(parse_file, 'w') as fout:
			for ii, line in enumerate(article):
				printr(f'{i+1:0{len(n)}}/{n}\t{parse_file}\t{ii}')
				fout.write(f'#{ii}:1.[0] S('+'|'.join(f'Head:{tag}:{txt}' for txt, tag in line.zip2)+')#\n')
	if not thrank: print()


if __name__ == '__main__':

	main()
	print()
	pass
