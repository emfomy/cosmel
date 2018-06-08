#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import json
import os
import sys

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *


def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Postprocesses HTML.')

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
	data_root    = f'data/{ver}'
	corpus_root  = f'data/{ver}/corpus/{date}'
	article_root = f'{corpus_root}/article/{target}_role'
	html_root    = f'{corpus_root}/html/html_article_notag'
	idx_root     = f'{corpus_root}/html/{target}_idx'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(article_root))
	if nth: parts = parts[thrank:len(parts):nth]

	# Map word-segmented articles to html articles
	html_files = glob_files(html_root, parts=parts)
	n = str(len(html_files))
	for i, html_file in enumerate(html_files):
		idx_file = transform_path(html_file, html_root, idx_root, '.idx')
		os.makedirs(os.path.dirname(idx_file), exist_ok=True)
		printr(f'{i+1:0{len(n)}}/{n}\t{idx_file}')

		article_file = transform_path(html_file, html_root, article_root, '.role')
		article = Article(article_file, article_root)

		with open(html_file) as fin, open(idx_file, 'w') as fout:
			html_data = fin.read()
			html_idx = -1
			for sid, line in enumerate(article):
				idx_line_list = []
				for mid, word in enumerate(line.txts):
					chars = ''.join(word.replace('□', ''))
					char = chars[0]
					html_idx = get_html_idx(html_data, char, html_idx)
					html_idx0 = html_idx
					for char in chars[1:]:
						html_idx = get_html_idx(html_data, char, html_idx)
					idx_line_list.append(f'{word}({html_idx0},{html_idx})')
				fout.write('　'.join(idx_line_list)+'\n')
	if not thrank: print()


def get_html_idx(html_data, word, start_idx):
	try:
		return html_data[(start_idx+1):].index(word)+(start_idx+1)
	except ValueError:
		return start_idx


if __name__ == '__main__':

	main()
	print()
	pass
