#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import os
import sys

import numpy as np

import torch

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *
from model.module.meta import *
from model.predict import check_accuracy

if __name__ == '__main__':

	# Parse arguments
	argparser = argparse.ArgumentParser(description='Test CosmEL model.')

	arggroup = argparser.add_mutually_exclusive_group()
	arggroup.add_argument('-v', '--ver', metavar='<ver>#<date>', \
			help='set <dir> as "data/<ver>/model/<date>"')
	arggroup.add_argument('-D', '--dir', metavar='<dir>', \
			help='prepend <dir> to data and model path')

	argparser.add_argument('-d', '--data', metavar='<data_name>', required=True, \
			help='testing data path; load data from "[<dir>]<data_name>.list.txt"')
	argparser.add_argument('--meta', metavar='<meta_name>', \
			help='dataset meta path; default is "[<dir>/]meta.pkl"')

	argparser.add_argument('-c', '--check', action='store_true', help='Check arguments.')

	args = argparser.parse_args()

	vers          = args.ver.split('#')
	assert len(vers) == 2, argparser.format_usage()
	ver           = vers[0]
	date          = vers[1]

	data_root     = f'data/{ver}'

	result_root = ''
	if args.ver != None:
		result_root = f'{data_root}/model/{date}'
	if args.dir != None:
		result_root = f'{args.dir}'

	data_file     = f'{result_root}/{args.data}.list.txt'

	meta_file     = f'{result_root}/meta.pkl'
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
	# asmid_list.rid_to_mtype()
	# asmid_list.gid_to_mtype()
	# asmid_list.filter_sp()
	print()
	pred_gid = np.asarray([asmid.rid for asmid in asmid_list])
	true_gid = np.asarray([asmid.gid for asmid in asmid_list])

	# Set batch size
	num_test = len(asmid_list)
	print(f'num_test = {num_test}')

	repo    _         = meta.new_repo()
	corpus, ment_list = asmid_list.new_corpus()

	rule_list = np.asarray([m.rule for m in ment_list])
	true_gid = true_gid[rule_list == 'P_rule1']
	pred_gid = pred_gid[rule_list == 'P_rule1']

	# # Check accuracy
	# check_accuracy(true_gid, pred_gid)

	from sklearn.metrics import accuracy_score, f1_score
	acc     = np.zeros((5,))
	acc[0]  = accuracy_score(true_gid, pred_gid)
	acc[1]  = f1_score(true_gid, pred_gid, average='weighted')
	acc[2:] = f1_score(true_gid, pred_gid, average=None, labels=['PID', 'OSP', 'GP'])
	acc = acc*100

	np.set_printoptions(formatter={'float_kind': (lambda x: f'{x:05.2f}')})
	print()
	print('  acc   f1    PID   OSP   GP')
	print(acc)

	pass
