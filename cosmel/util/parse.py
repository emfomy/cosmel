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

	argparser.add_argument('-c', '--corpus', required=True,
			help='store corpus data in directory "<CORPUS>/"')
	argparser.add_argument('-t', '--thread', type=int, \
			help='use <THREAD> threads; default is `os.cpu_count()`')
	argparser.add_argument('-h', '--host',
			help='connect to host with IP <HOST>')
	argparser.add_argument('-p', '--port',
			help='connect to host with port <PORT>')

	args = argparser.parse_args()

	corpus_root = os.path.normpath(args.corpus)

	host = args.host
	port = args.port

	nth = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print(f'Use {nth} threads')

	import multiprocessing
	with multiprocessing.Pool(nth) as pool:
		results = [pool.apply_async(submain, args=(corpus_root, nth, thrank, host, port)) for thrank in range(nth)]
		[result.get() for result in results]
		del results


def submain(corpus_root, nth=None, thrank=0, host=None, port=None):

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
				fout.write('\t'.join(parse(line, host=host, port=port))+'\n')
	if not thrank: print()

def parse(line, host=None, port=None):
	uname = '_tester'
	pwd   = 'tester'
	return list(itertools.chain.from_iterable(ckipparser.parse(str(line[i:i+80]), uname, pwd, ws=True, host=host, port=port) \
			for i in range(0, len(line), 80)))


if __name__ == '__main__':

	main()
	print()
	pass
