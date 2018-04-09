#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import os
import sys

import numpy as np

import keras.models

from gensim.models.keyedvectors import KeyedVectors

sys.path.insert(0, os.path.abspath('.'))
from styleme import *
from data import DataPack
from predict import model_accuracy

if __name__ == '__main__':

	argparser = argparse.ArgumentParser(description='Test StyleMe rule.')

	arggroup = argparser.add_mutually_exclusive_group()
	arggroup.add_argument('-v', '--ver', metavar='<ver>#<date>', \
			help='set <dir> as "result/<ver>_<date>"')
	arggroup.add_argument('-D', '--dir', metavar='<dir>', \
			help='prepend <dir> to data and model path')
	argparser.add_argument('-E', '--ext', action='store_true', \
			help='append extensions to data and model path; use ".data.pkl" for data, and ".model.h5" for model.')

	argparser.add_argument('-d', '--data', metavar='<data_path>', required=True, \
			help='testing data path; load data from "[<dir>]<data_path>[.data.pkl]"')

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
		result_root = args.dir

	data_ext      = ''
	if args.ext:
		data_ext    = '.data.pkl'

	data_file     = f'{result_root}{args.data}{data_ext}'

	# Print arguments
	print()
	print(args)
	print()
	print(f'data_file  = {data_file}')
	print()

	if args.check: exit()

	# Load data
	pack = DataPack.load(data_file)
	num_test = pack.data.gid_code.shape[0]
	print(f'num_test = {num_test}')

	# Check accuracy of PID
	model_accuracy(pack.data.pid, pack.data.gid)
	model_accuracy(pack.data.pid, pack.data.gid, pack.data.rule == 'P_rule1', 'P_rule1')

	pass
