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
from data import DataPack
from model2 import Model2 as Model

def model_accuracy(predict_gid_code, true_gid_code, mask=slice(None,None), name='all'):
	correct = (true_gid_code[mask] == predict_gid_code[mask])
	accuracy = correct.sum() / correct.size
	print(f'accuracy ({name}) = {accuracy} ({correct.sum()}/{correct.size})')

if __name__ == '__main__':

	# Parse arguments
	argparser = argparse.ArgumentParser(description='Test StyleMe model.')

	arggroup = argparser.add_mutually_exclusive_group()
	arggroup.add_argument('-v', '--ver', metavar='<ver>#<date>', \
			help='set <dir> as "result/<ver>_<date>"')
	arggroup.add_argument('-D', '--dir', metavar='<dir>', \
			help='prepend <dir> to data and model path')

	argparser.add_argument('-d', '--data', metavar='<data_name>', required=True, \
			help='testing data path; load data from "[<dir>]<data_name>.data.pkl"')
	argparser.add_argument('-m', '--model', metavar='<model_name>', \
			help='model path; load model into "[<dir>]<model_name>.model.pt"')

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

	data_file     = f'{result_root}{args.data}.data.pkl'
	model_file    = f'{result_root}{args.model}.model.pt'

	# Print arguments
	print()
	print(args)
	print()
	print(f'data_file  = {data_file}')
	print(f'model_file = {model_file}')
	print()

	if args.check: exit()

	# Load data
	pack = DataPack.load(data_file)
	num_test = pack.data.gid_code.shape[0]
	print(f'num_test        = {num_test}')
	print()

	# Load model
	model = Model(pack.info)
	print()
	model.load(model_file)
	print(f'Loaded model from "{model_file}"')
	print()

	# Create inputs
	inputs = model.inputs(pack)

	# Use GPU
	model.cuda()
	inputs.cuda()

	# Apply model
	predict_prob = model.predict(**vars(inputs)).cpu().data.numpy()
	predict_gid_code = np.argmax(predict_prob, axis=1)
	model_accuracy(predict_gid_code, pack.data.gid_code)
	model_accuracy(predict_gid_code, pack.data.gid_code, pack.data.rule == 'P_rule1', 'P_rule1')

	pass
