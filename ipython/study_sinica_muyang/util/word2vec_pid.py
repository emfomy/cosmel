#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import itertools
import os
import sys

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *

if __name__ == '__main__':

	assert len(sys.argv) > 1
	ver = sys.argv[1]

	data_root    = f'data/{ver}'
	target       = f'pruned_article'
	target_ver   = f'_pid'
	repo_root    = f'{data_root}/repo'
	article_root = f'{data_root}/article/{target}_role'
	mention_root = f'{data_root}/mention/{target}{target_ver}'
	txt_file     = f'{data_root}/embedding/{target}_pid.txt'
	parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) > 2: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	repo   = Repo(repo_root)
	corpus = Corpus(article_root, mention_root=mention_root, parts=parts)

	# Replace mention
	n = str(len(corpus.mention_set))
	for i, m in enumerate(corpus.mention_set):
		printr(f'{i+1:0{len(n)}}/{n}\t{m.asmid}')
		if m.pid.isdigit():
			m.sentence.txts[m.start_idx] = 'PID'+m.pid
	print()

	N = 10

	# Concatenate articles
	os.makedirs(os.path.dirname(txt_file), exist_ok=True)
	with open(txt_file, 'w') as fout:

		# Product ID
		n = str(len(repo.product_set))
		for i, p in enumerate(repo.product_set):
			printr(f'{i+1:0{len(n)}}/{n}\tProcessing {p}')
			for _ in range(N):
				fout.write(f'PID{p.pid}\n')
		print()

		# Brand Name
		n = str(len(repo.brand_set))
		for i, b in enumerate(repo.brand_set):
			printr(f'{i+1:0{len(n)}}/{n}\tProcessing {b}')
			for _ in range(N):
				fout.write(' '.join(list(b))+'\n')
		print()

		# Infix Name
		n = str(len(repo.infix_set))
		for i, x in enumerate(repo.infix_set):
			printr(f'{i+1:0{len(n)}}/{n}\tProcessing {x}')
			for _ in range(N):
				fout.write(f'{x}\n')
		print()

		# Head Name
		n = str(len(repo.head_set))
		for i, x in enumerate(repo.head_set):
			printr(f'{i+1:0{len(n)}}/{n}\tProcessing {x}')
			for _ in range(N):
				fout.write(f'{x}\n')
		print()

		# Product Name
		n = str(len(repo.product_set))
		for i, p in enumerate(repo.product_set):
			printr(f'{i+1:0{len(n)}}/{n}\tProcessing {p}')
			for _ in range(N):
				fout.write(' '.join(list(p.name_ws.txts))+'\n')
		print()

		# Product Description
		n = str(len(repo.product_set))
		for i, p in enumerate(repo.product_set):
			printr(f'{i+1:0{len(n)}}/{n}\tProcessing {p}')
			fout.write(' '.join(list(p.descr_ws.txts))+'\n')
		print()

		# Corpus
		n = str(len(corpus.article_set))
		for i, article in enumerate(corpus.article_set):
			printr(f'{i+1:0{len(n)}}/{n}\tProcessing {article.path}')
			for sentence in article:
				fout.write(' '.join(sentence.txts)+'\n')
	print()
	print(f'Output word2vec corpus to "{txt_file}"')

	pass
