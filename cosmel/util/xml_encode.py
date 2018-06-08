#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import argparse
import os
import sys

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *


def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Encode XML.')

	argparser.add_argument('-v', '--ver', metavar='<ver>#<date>', required=True, \
			help='load repo from "data/<ver>", and load/save corpus data from/into "data/<ver>/corpus/<date>"')

	argparser.add_argument('-i', '--input', metavar='<in_dir>', required=True, \
			help='load mention from "data/<ver>/mention/<in_dir>"')
	argparser.add_argument('-o', '--output', metavar='<out_dir>', \
			help='dump XML into "data/<ver>/xml/<out_dir>"; default is <in_dir>')

	argparser.add_argument('-t', '--thread', metavar='<thread>', type=int, \
			help='use <thread> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	vers = args.ver.split('#')
	assert len(vers) == 2, argparser.format_usage()
	ver  = vers[0]
	date = vers[1]
	assert len(ver)  > 0
	assert len(date) > 0

	in_dir  = args.input
	out_dir = args.output
	if not out_dir:
		out_dir = in_dir

	nth     = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print(f'Use {nth} threads')

	import multiprocessing
	with multiprocessing.Pool(nth) as pool:
		results = [pool.apply_async(submain, args=(ver, date, in_dir, out_dir, nth, thrank,)) for thrank in range(nth)]
		[result.get() for result in results]
		del results


def submain(ver, date, in_dir, out_dir, nth=None, thrank=0):

	target       = f'purged_article'
	data_root    = f'data/{ver}'
	corpus_root  = f'data/{ver}/corpus/{date}'
	repo_root    = f'{data_root}/repo'
	article_root = f'{corpus_root}/article/{target}_role'
	mention_root = f'{corpus_root}/mention/{in_dir}'
	xml_root     = f'{corpus_root}/xml/{out_dir}'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(article_root))
	if nth: parts = parts[thrank:len(parts):nth]

	# Load CosmEL repository and corpus
	corpus = Corpus(article_root, mention_root=mention_root, parts=parts)

	# Extract html from json
	n = str(len(corpus.mention_bundle_set))
	for i, bundle in enumerate(corpus.mention_bundle_set):
		article = bundle.article
		xml_file = transform_path(article.path, article_root, xml_root, '.xml')

		os.makedirs(os.path.dirname(xml_file), exist_ok=True)
		printr(f'{i+1:0{len(n)}}/{n}\t{xml_file}')

		for mention in bundle:
			article[mention.sid].txts[mention.start_idx] = add_start_xml(article[mention.sid].txts[mention.start_idx], mention)
			article[mention.sid].txts[mention.last_idx]  = add_end_xml(article[mention.sid].txts[mention.last_idx],    mention)

		article.save(xml_file, txtstr)
	if not thrank: print()


def add_start_xml(start, mention):
	return mention.start_xml + start

def add_end_xml(end, mention):
	return end + mention.end_xml

if __name__ == '__main__':

	main()
	print()
	pass
