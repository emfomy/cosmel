#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <http://muyang.pro>'
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

	target       = f'purged_article'
	repo_root    = f'{corpus_root}/repo'
	article_root = f'{corpus_root}/article/{target}_role'
	mention_root = f'{corpus_root}/mention/{target}'
	output_root  = f'{corpus_root}/mention/{target}_rid'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(article_root))
	if nth: parts = parts[thrank:len(parts):nth]
	if not parts: return

	repo   = Repo(repo_root)
	corpus = Corpus(article_root, mention_root=mention_root, parts=parts)


	n = str(len(corpus.mention_bundle_set))
	for i, bundle in enumerate(corpus.mention_bundle_set):
		output_file = transform_path(bundle.path, mention_root, output_root, '.json')
		printr(f'{i+1:0{len(n)}}/{n}\t{output_file}')
		for mention in bundle:
			try:
				bidx  = len(mention.sentence_pre.roles) - list(reversed(mention.sentence_pre.roles)).index('Brand') - 1
				brand = mention.sentence_pre.txts[bidx]
			except ValueError:
				continue
			else:
				m_infix = ''.join(mention.sentence_pre.txts[bidx+1:])
				candidates = repo.bname_head_to_product_list[brand, mention.head]
				for c in candidates:
					if ''.join(c.infix_ws.txts) == m_infix:
						mention.set_rid(c.pid)
						mention.set_rule('P_rule1')
						break
		bundle.save(output_file)
	if not thrank: print()


if __name__ == '__main__':

	main()
	print()
	pass
