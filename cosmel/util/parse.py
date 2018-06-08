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
	argparser = argparse.ArgumentParser(description='CosmEL: Parse Sentence.')

	argparser.add_argument('-v', '--ver', metavar='<ver>#<cver>', required=True, \
			help='load repo from "data/<ver>", and load/save corpus data from/into "data/<ver>/corpus/<cver>"')
	argparser.add_argument('-t', '--thread', metavar='<thread>', type=int, \
			help='use <thread> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	vers = args.ver.split('#')
	assert len(vers) == 2, argparser.format_usage()
	ver  = vers[0]
	cver = vers[1]
	assert len(ver)  > 0
	assert len(cver) > 0

	nth = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print(f'Use {nth} threads')

	import multiprocessing
	with multiprocessing.Pool(nth) as pool:
		results = [pool.apply_async(submain, args=(ver, cver, nth, thrank,)) for thrank in range(nth)]
		[result.get() for result in results]
		del results


def submain(ver, cver, nth=None, thrank=0):

	target       = f'purged_article'
	target_parse = f'parsed_article'
	data_root    = f'data/{ver}'
	corpus_root  = f'data/{ver}/corpus/{cver}'
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
				fout.write('\t'.join(parse(line))+'\n')
	if not thrank: print()

def parse(line):
	uname = '_tester'
	pwd   = 'tester'
	return list(itertools.chain.from_iterable(ckipparser.parse(str(line[i:i+80]), uname, pwd, True) \
			for i in range(0, len(line), 80)))


if __name__ == '__main__':

	main()
	print()
	pass
