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
	argparser = argparse.ArgumentParser(description='Split CosmEL training/testing data.')

	argparser.add_argument('-v', '--ver', metavar='<ver>#<date>', required=True, \
			help='CosmEL corpus version; load data from "data/<ver>", and load mention from "data/<ver>/pruned_article_gid_<date>"')
	argparser.add_argument('-D', '--dir', metavar='<dir>', \
			help='data path prefix; output data into "<dir>/"; default is "result/<ver>_<date>"')
	argparser.add_argument('-e', '--embedding', metavar='<embedding_path>', \
			help='embedding path; default is "data/<ver>/embedding/pruned_article.dim300.emb.bin."')

	arggroup = argparser.add_mutually_exclusive_group()
	arggroup.add_argument('-p', '--parts', metavar='<part>', nargs='+', help='parts of corpus')
	arggroup.add_argument('-n', '--num-parts', metavar='<num>', type=int, help='number of parts (override --parts)')

	argparser.add_argument('-c', '--check', action='store_true', help='check arguments ')

	args = argparser.parse_args()

	vers          = args.ver.split('#')
	ver           = vers[0]
	date          = ''
	if len(vers) > 1:
		date        = f'_{vers[1]}'

	result_root   = f'result/{ver}{date}/'
	if args.dir != None:
		result_root = f'{args.dir}/'

	parts         = ['']
	if args.parts != None:
		parts       = args.parts
	if args.num_parts != None:
		parts       = list(f'part-{x:05}' for x in range(args.num_parts))

	data_root     = f'data/{ver}/'
	repo_root     = f'{data_root}repo'
	article_root  = f'{data_root}article/pruned_article_role'
	mention_root  = f'{data_root}mention/pruned_article_gid{date}'
	bad_article   = f'{data_root}article/bad_article.txt'

	emb_file      = f'{data_root}embedding/pruned_article.dim300.emb.bin'
	if args.embedding != None:
		emb_file    = embedding.parts

	meta_file            = f'{result_root}meta.pkl'
	pid_asmid_file       = f'{result_root}pid.all.list.txt'
	gid_asmid_file       = f'{result_root}gid.all.list.txt'
	pid_asmid_train_file = f'{result_root}pid.train.list.txt'
	pid_asmid_test_file  = f'{result_root}pid.test.list.txt'
	gid_asmid_train_file = f'{result_root}gid.train.list.txt'
	gid_asmid_test_file  = f'{result_root}gid.test.list.txt'

	# Print arguments
	print()
	print(args)
	print()
	print(f'repo_root           = {repo_root}')
	print(f'article_root        = {article_root}')
	print(f'mention_root        = {mention_root}')
	print(f'emb_file            = {emb_file}')
	print(f'parts               = {parts}')
	print()
	print(f'meta_file            = {meta_file}')
	print(f'pid_asmid_file       = {pid_asmid_file}')
	print(f'gid_asmid_file       = {gid_asmid_file}')
	print(f'pid_asmid_train_file = {pid_asmid_train_file}')
	print(f'pid_asmid_test_file  = {pid_asmid_test_file}')
	print(f'gid_asmid_train_file = {gid_asmid_train_file}')
	print(f'gid_asmid_test_file  = {gid_asmid_test_file}')
	print()

	if args.check: exit()

	# Load CosmEL repository and corpus
	with open(bad_article) as fin:
		skip_list = fin.read().strip().split('\n')
	repo   = Repo(repo_root)
	corpus = Corpus(article_root, mention_root=mention_root, parts=parts, skips=skip_list)
	print()

	# Prepare dataset meta
	meta = DataSetMeta.new(repo, corpus, emb_file)
	meta.dump(meta_file)

	if len(corpus.mention_set) == 0:

		print('\nIgnore asmid list generation.')

	else:

		# Merge NAP and GP
		for m in corpus.mention_set:
			if m.gid == 'NAP': m.set_gid('GP')
			if m.pid == 'NAP': m.set_pid('GP')

		# Load mention list
		pid_asmid_list = AsmidList([Asmid(aid=m.aid, sid=m.sid, mid=m.mid, gid=m.pid, pid=m.pid) \
				for m in corpus.mention_set if m.pid])
		gid_asmid_list = AsmidList([Asmid(aid=m.aid, sid=m.sid, mid=m.mid, gid=m.gid, pid=m.pid) \
				for m in corpus.mention_set if m.gid])

		pid_asmid_train_list, pid_asmid_test_list = pid_asmid_list.train_test_split(test_size=0.3, random_state=0, shuffle=True)
		gid_asmid_train_list, gid_asmid_test_list = gid_asmid_list.train_test_split(test_size=0.3, random_state=0, shuffle=True)

		pid_asmid_list.dump(pid_asmid_file)
		gid_asmid_list.dump(gid_asmid_file)
		pid_asmid_train_list.dump(pid_asmid_train_file)
		pid_asmid_test_list.dump(pid_asmid_test_file)
		gid_asmid_train_list.dump(gid_asmid_train_file)
		gid_asmid_test_list.dump(gid_asmid_test_file)

	pass
