#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Chi-Yen Chen <jina199312@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import os
import subprocess
import sys

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *


def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Annotate by Rule (Exact Match).')

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

	# submain(ver, date)


def submain(ver, cver, nth=None, thrank=0):

	target       = f'purged_article'
	data_root    = f'data/{ver}'
	corpus_root  = f'data/{ver}/corpus/{cver}'
	repo_root    = f'{data_root}/repo'
	article_root = f'{corpus_root}/article/{target}_role'
	mention_root = f'{corpus_root}/mention/{target}'
	output_root  = f'{corpus_root}/mention/{target}_rid'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(article_root))
	if nth: parts = parts[thrank:len(parts):nth]

	repo   = Repo(repo_root)
	corpus = Corpus(article_root, mention_root=mention_root, parts=parts)

	# from IPython import embed
	# embed()

	n = str(len(corpus.mention_bundle_set))
	for i, bundle in enumerate(corpus.mention_bundle_set):
		output_file = transform_path(bundle.path, article_root, output_root, '.json')
		printr(f'{i+1:0{len(n)}}/{n}\t{output_file}')
		for mention in bundle:
			# printr(f'current mention: {mention}\n')
			if not 'Brand' in mention.sentence_pre.roles: continue

			idx  = list(reversed(mention.sentence_pre.roles)).index('Brand')
			brand = list(reversed(mention.sentence_pre.txts))[idx]
			print(f'mention: {mention}, idx: {idx}, brand: {brand}')
			candidate = repo.bname_head_to_product_list[list(reversed(mention.sentence_pre.txts))[idx], mention.head]
			# print(f'candidate: {candidate}')
			prob_infix = ''.join(s for s in mention.sentence.txts[list(mention.sentence.txts).index(brand)+1 : list(mention.sentence.txts).index(mention.head)])
			# print(f'prob_infix: {prob_infix}')
			for c in candidate:
				# printr(f'current candidate: {c}')
				infix = ''.join(i for i in c.infix_ws.txts)
				if prob_infix == infix:
					print(f'exact: {c}')
					mention.set_rid(c.pid)
					break

		bundle.save(output_file)
	if not thrank: print()


if __name__ == '__main__':

	main()
	print()
	pass
