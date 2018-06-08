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

	argparser.add_argument('-v', '--ver', metavar='<ver>#<date>', required=True, \
			help='CosmEL corpus version; load data from "data/<ver>", and load mention from "data/<ver>/purged_article_gid_<date>"')
	argparser.add_argument('-D', '--dir', metavar='<dir>', \
			help='data path prefix; output data into "<dir>/"; default is "data/<ver>/model/<date>"')
	argparser.add_argument('--emb', metavar='<embedding_path>', \
			help='embedding path; default is "data/<ver>/embedding/purged_article.dim300.emb.bin"')

	arggroup = argparser.add_mutually_exclusive_group()
	arggroup.add_argument('-p', '--parts', metavar='<part>', nargs='+', help='parts of corpus')
	arggroup.add_argument('-n', '--num-parts', metavar='<num>', type=int, help='number of parts (override --parts)')

	argparser.add_argument('-c', '--check', action='store_true', help='check arguments')

	args = argparser.parse_args()

	vers = args.ver.split('#')
	assert len(vers) == 2, argparser.format_usage()
	ver  = vers[0]
	date = vers[1]

	data_root = f'data/{ver}'

	result_root = f'{data_root}/model/{date}'
	if args.dir != None:
		result_root = f'{args.dir}'

	parts = ['']
	if args.parts != None:
		parts = args.parts
	if args.num_parts != None:
		parts = list(f'part-{x:05}' for x in range(args.num_parts))

	repo_root    = f'{data_root}/repo'
	article_root = f'{data_root}/article/purged_article_role'
	mention_root = f'{data_root}/mention/purged_article_gid_{date}'
	bad_article  = f'{data_root}/article/bad_article.txt'

	emb_file = f'{data_root}/embedding/purged_article.dim300.emb.bin'
	if args.emb != None:
		emb_file = args.emb

	meta_file            = f'{result_root}/meta.pkl'
	nil_asmid_file       = f'{result_root}/nil.list.txt'
	gid_asmid_file       = f'{result_root}/gid.list.txt'
	rid_asmid_file       = f'{result_root}/rid.list.txt'

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
	print(f'nil_asmid_file       = {nil_asmid_file}')
	print(f'gid_asmid_file       = {gid_asmid_file}')
	print(f'rid_asmid_file       = {rid_asmid_file}')
	print()

	if args.check: exit()

	# Load CosmEL repository and corpus
	with open(bad_article) as fin:
		skip_list = fin.read().strip().split('\n')
	repo   = Repo(repo_root)
	corpus = Corpus(article_root, mention_root=mention_root, parts=parts, skips=skip_list)
	print()

	# Prepare dataset meta
	meta = DataSetMeta.new(repo, emb_file)
	meta.dump(meta_file)

	if len(corpus.mention_set) == 0:

		print('\nIgnore asmid list generation.')

	else:

		# Merge NAP and GP
		for m in corpus.mention_set:
			if m.gid == 'NAP': m.set_gid('GP')
			if m.nid == 'NAP': m.set_nid('GP')
			if m.rid == 'NAP': m.set_rid('GP')

		# Load mention list
		nil_asmid_list = AsmidList(corpus.article_set.path, corpus.mention_set.path, \
				(Asmid(aid=m.aid, sid=m.sid, mid=m.mid, gid=m.gid, nid=m.nid, rid=m.rid, rule=m.rule) for m in corpus.mention_set))
		gid_asmid_list = AsmidList(corpus.article_set.path, corpus.mention_set.path, \
				(Asmid(aid=m.aid, sid=m.sid, mid=m.mid, gid=m.gid, rid=m.rid, rule=m.rule) for m in corpus.mention_set if m.gid))
		rid_asmid_list = AsmidList(corpus.article_set.path, corpus.mention_set.path, \
				(Asmid(aid=m.aid, sid=m.sid, mid=m.mid, gid=m.rid, rid=m.rid, rule=m.rule) for m in corpus.mention_set if m.rid))

		nil_asmid_list.dump(nil_asmid_file)
		gid_asmid_list.dump(gid_asmid_file)
		rid_asmid_list.dump(rid_asmid_file)

	pass
