#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import itertools
import json
import os
import pickle
import sys

from sklearn.model_selection import train_test_split

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *
from model.module.meta import *


if __name__ == '__main__':

	# Parse arguments
	argparser = argparse.ArgumentParser(description='Generate CosmEL meta data.')


	argparser.add_argument('-c', '--corpus', required=True,
		help='store corpus data in directory "<CORPUS>/"')
	argparser.add_argument('-m', '--model', required=True,
		help='store model data in directory "<MODEL>/"')

	argparser.add_argument('--emb', \
			help='embedding path; default is "<CORPUS>/embedding/purged_article.dim300.emb.bin"')

	argparser.add_argument('-k', '--check', action='store_true', help='check arguments')

	args = argparser.parse_args()

	corpus_root = os.path.normpath(args.corpus)
	model_root  = os.path.normpath(args.model)

	repo_root   = f'{corpus_root}/repo'

	emb_file = f'{corpus_root}/embedding/purged_article.dim300.emb.bin'
	if args.emb != None:
		emb_file = args.emb

	meta_file = f'{model_root}/meta.pkl'

	# Print arguments
	print()
	print(args)
	print()
	print(f'repo_root   = {repo_root}')
	print(f'corpus_root = {corpus_root}')
	print(f'model_root  = {model_root}')
	print(f'emb_file    = {emb_file}')
	print(f'meta_file   = {meta_file}')
	print()

	if args.check: sys.exit()

	# Prepare dataset meta
	repo = Repo(repo_root)
	meta = DataSetMeta.new(repo, emb_file)
	meta.dump(meta_file)

	pass
