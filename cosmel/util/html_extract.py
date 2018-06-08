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

	etc_root     = f'etc'
	data_root    = f'data/{ver}'
	corpus_root  = f'data/{ver}/corpus/{date}'
	json_root    = f'{corpus_root}/html/article_filtered'
	html_root    = f'{corpus_root}/html/html_article'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(json_root))
	if nth: parts = parts[thrank:len(parts):nth]

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
