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

	argparser.add_argument('-c', '--corpus', required=True,
			help='store corpus data in directory "<CORPUS>/"')

	argparser.add_argument('-i', '--input', required=True, \
			help='load mention from "<CORPUS>/mention/<INPUT>/"')
	argparser.add_argument('-o', '--output', \
			help='dump XML into "<CORPUS>/xml/<OUTPUT>/"; default is <INPUT>')

	argparser.add_argument('-t', '--thread', type=int, \
			help='use <THREAD> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	corpus_root = os.path.normpath(args.corpus)

	in_dir  = args.input
	out_dir = args.output
	if not out_dir:
		out_dir = in_dir

	nth     = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print(f'Use {nth} threads')

	import multiprocessing
	jobs = [multiprocessing.Process(target=submain, args=(corpus_root, in_dir, out_dir, nth, thrank,)) for thrank in range(nth)]
	for p in jobs: p.start()
	for p in jobs: p.join()
	for p in jobs: assert p.exitcode == 0


def submain(corpus_root, in_dir, out_dir, nth=None, thrank=0):

	target       = f'purged_article'
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
