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

	argparser.add_argument('-v', '--ver', metavar='<ver>#<cver>#<mver>', required=True, \
		help='load repo from "data/<ver>/", load corpus data from "data/<ver>/corpus/<cver>/", ' + \
				'and load/save model data from/into "data/<ver>/model/<mver>/"; the default value of <mver> is <cver>')
	argparser.add_argument('--emb', metavar='<embedding_path>', \
			help='embedding path; default is "data/<ver>/corpus/<cver>/embedding/purged_article.dim300.emb.bin"')

	argparser.add_argument('-c', '--check', action='store_true', help='check arguments')

	args = argparser.parse_args()

	vers = args.ver.split('#')
	assert 2 <= len(vers) <= 3, argparser.format_usage()
	ver  = vers[0]
	cver = vers[1]
	mver = vers[-1]
	assert len(ver)  > 0
	assert len(cver) > 0
	assert len(mver) > 0

	data_root   = f'data/{ver}'
	corpus_root = f'data/{ver}/corpus/{cver}'
	model_root  = f'data/{ver}/model/{mver}'

	repo_root   = f'{data_root}/repo'

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

	if args.check: exit()

	# Prepare dataset meta
	repo = Repo(repo_root)
	meta = DataSetMeta.new(repo, emb_file)
	meta.dump(meta_file)

	pass
