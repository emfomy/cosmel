#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import itertools
import os
import sys

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *

from xml_encode import add_start_xml
from xml_encode import add_end_xml


def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Encode HTML.')

	argparser.add_argument('-v', '--ver', metavar='<ver>#<cver>', required=True, \
			help='load repo from "data/<ver>", and load/save corpus data from/into "data/<ver>/corpus/<cver>"')

	argparser.add_argument('-i', '--input', metavar='<in_dir>', required=True, \
			help='load mention from "data/<ver>/corpus/<cver>/mention/<in_dir>"')
	argparser.add_argument('-o', '--output', metavar='<out_dir>', \
			help='dump XML into "data/<ver>/html/<out_dir>"; default is <in_dir>')

	argparser.add_argument('-t', '--thread', metavar='<thread>', type=int, \
			help='use <thread> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	vers = args.ver.split('#')
	assert len(vers) == 2, argparser.format_usage()
	ver  = vers[0]
	cver = vers[1]
	assert len(ver)  > 0
	assert len(cver) > 0

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
		results = [pool.apply_async(submain, args=(ver, cver, in_dir, out_dir, nth, thrank,)) for thrank in range(nth)]
		[result.get() for result in results]
		del results


def submain(ver, cver, in_dir, out_dir, nth=None, thrank=0):

	target       = f'purged_article'
	data_root    = f'data/{ver}'
	corpus_root  = f'data/{ver}/corpus/{cver}'
	repo_root    = f'{data_root}/repo'
	html_root    = f'{corpus_root}/html/html_article'
	idx_root     = f'{corpus_root}/html/{target}_idx'
	mention_root = f'{corpus_root}/mention/{in_dir}'
	output_root  = f'{corpus_root}/html/{out_dir}'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(html_root))
	if nth: parts = parts[thrank:len(parts):nth]

	# Load CosmEL repository and corpus
	corpus = Corpus(idx_root, mention_root=mention_root, parts=parts)

	# Extract html from json
	html_files = glob_files(html_root, parts)
	n = str(len(html_files))
	for i, html_file in enumerate(html_files):
		output_file = transform_path(html_file, html_root, output_root, '.xml.html')
		os.makedirs(os.path.dirname(output_file), exist_ok=True)
		printr(f'{i+1:0{len(n)}}/{n}\t{output_file}')

		with open(html_file) as fin, open(output_file, 'w') as fout:
			output_data = list(fin.read())
			bundle = corpus.id_to_mention_bundle[Article.path_to_aid(html_file, html_root)]

			for mention in bundle:
				idx0, idx1 = get_html_idxs(mention)
				output_data[idx0] = add_start_xml(output_data[idx0], mention)
				output_data[idx1] = add_end_xml(output_data[idx1], mention)

			fout.write(f'<!--{ver}-->\n'+''.join(output_data))
	if not thrank: print()


def get_html_idxs(mention):
	return (int(mention.sentence.tags[mention.start_idx].split(',')[0]), \
			int(mention.sentence.tags[mention.last_idx].split(',')[1]))


if __name__ == '__main__':

	main()
	print()
	pass
