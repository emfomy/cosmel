#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import os
import sys

import numpy as np

import torch

sys.path.insert(0, os.path.abspath('.'))
from styleme import *
from meta import *
from predict import check_accuracy

if __name__ == '__main__':

	# Parse arguments
	argparser = argparse.ArgumentParser(description='Test StyleMe model.')

	arggroup = argparser.add_mutually_exclusive_group()
	arggroup.add_argument('-v', '--ver', metavar='<ver>#<date>', \
			help='set <dir> as "result/<ver>_<date>"')
	arggroup.add_argument('-D', '--dir', metavar='<dir>', \
			help='prepend <dir> to data and model path')

	argparser.add_argument('-d', '--data', metavar='<data_name>', required=True, \
			help='testing data path; load data from "[<dir>]<data_name>.list.txt"')
	argparser.add_argument('--meta', metavar='<meta_name>', \
			help='dataset meta path; default is "[<dir>/]meta.pkl"')

	argparser.add_argument('-c', '--check', action='store_true', help='Check arguments.')

	args = argparser.parse_args()

	vers          = args.ver.split('#')
	ver           = vers[0]
	date          = ''
	if len(vers) > 1:
		date        = f'_{vers[1]}'

	result_root = ''
	if args.ver != None:
		result_root = f'result/{ver}{date}/'
	if args.dir != None:
		result_root = f'{args.dir}/'

	data_file     = f'{result_root}{args.data}.list.txt'

	meta_file     = f'{result_root}meta.pkl'
	if args.meta != None:
		meta_file = args.meta

	# Print arguments
	print()
	print(args)
	print()
	print(f'data_file = {data_file}')
	print()

	if args.check: exit()

	############################################################################################################################
	# Load data
	#

	meta       = DataSetMeta.load(meta_file)
	asmid_list = AsmidList.load(data_file)
	print()
	pred_gid = np.asarray([asmid.pid for asmid in asmid_list])
	true_gid = np.asarray([asmid.gid for asmid in asmid_list])

	# Set batch size
	num_test = len(asmid_list)
	print(f'num_test = {num_test}')

	# parts  = list(set(m.aid for m in asmid_list))
	# repo   = Repo(meta.repo_path)
	# corpus = Corpus(meta.article_path, mention_root=meta.mention_path, parts=parts)

	# ment_list = [corpus.id_to_mention[asmid.asmid] for asmid in asmid_list]
	# for m, asmid in zip(ment_list, asmid_list):
	# 	m.set_gid(asmid.gid)
	# 	m.set_pid(asmid.pid)

	# rule_list = np.asarray([m.rule for m in ment_list])
	# check_accuracy(true_gid[rule_list == 'P_rule1'], pred_gid[rule_list == 'P_rule1'])

	# Check accuracy
	check_accuracy(true_gid, pred_gid)

	pass
