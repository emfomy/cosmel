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
from predict import model_accuracy
from module.dataset import MentionDataSet

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

	# Load dataset
	meta       = DatasetMeta.load(meta_file)
	asmid_list = AsmidList.load(data_file)
	print()
	dataset    = MentionDataSet(type('', (object,), {'meta': meta}), asmid_list)

	# Set batch size
	num_test = len(dataset)
	print(f'num_test = {num_test}')

	# Concatenate result
	raw_data = dataset.raw(None)
	pred_gid = raw_data.pid
	true_gid = raw_data.gid

	# Check accuracy
	model_accuracy(pred_gid, true_gid, slice(None,None),                'accuracy       ')

	model_accuracy(pred_gid, true_gid, [i.isdigit() for i in pred_gid], 'precision (PID)')
	model_accuracy(pred_gid, true_gid, [i.isdigit() for i in true_gid], 'recall    (PID)')

	model_accuracy(pred_gid, true_gid, pred_gid == 'OSP',               'precision (OSP)')
	model_accuracy(pred_gid, true_gid, true_gid == 'OSP',               'recall    (OSP)')

	model_accuracy(pred_gid, true_gid, pred_gid == 'GP',                'precision (GP) ')
	model_accuracy(pred_gid, true_gid, true_gid == 'GP',                'recall    (GP) ')

	pass
