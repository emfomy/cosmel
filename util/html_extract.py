#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import html
import json
import os
import re
import sys

from bs4 import BeautifulSoup

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *

def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Extracting HTML files.')

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

	etc_root     = f'etc'
	json_root    = f'{corpus_root}/html/article_filtered'
	html_root    = f'{corpus_root}/html/html_article'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(json_root))
	if nth: parts = parts[thrank:len(parts):nth]
	if not parts: return

	# Extract html from json
	for json_file in glob_files(json_root, parts):
		html_dir = json_file.replace(json_root, html_root)
		os.makedirs(html_dir, exist_ok=True)
		with open(json_file) as fin:
			for line in fin:
				json_data = json.loads(line)
				html_data = '\n'.join([
					'<!DOCTYPE html>',
					'<html>',
						'<head>',
							'<meta charset="UTF-8">',
						'</head>',
						'<body>',
							f'<center>{html.escape(json_data["title"])}</center>',
							'<hr>',
							json_data['content'],
						'</body>',
					'</html>',
				])
				aid = json_data['author'] + '_' + json_data['article_id']
				html_file = f'{html_dir}/{aid}.html'
				printr(html_file)
				with open(html_file, 'w') as fout:
					soup = BeautifulSoup(html_data, 'lxml')
					if aid in ['imsandra_28191442', 'imsandra_28166295', 'imsandra_28209327', 'imsandra_28096303']:
						for s in soup('strong'):
							for ss in s('strong'):
								ss.unwrap()
					fout.write(soup.prettify())
	if not thrank: print()


if __name__ == '__main__':

	main()
	print()
	pass
