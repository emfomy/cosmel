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

def model_load(model_file):
	predict_model = keras.models.load_model(model_file)
	print(f'Loaded model from "{model_file}"')
	predict_model.summary()
	return predict_model

def model_predict(predict_model, pack):
	predict_gid_code = np.argmax(predict_model.predict({
			'title_code': pack.data.title_code, \
			'pre_code':   pack.data.pre_code, \
			'post_code':  pack.data.post_code, \
			'pid_bag':    pack.data.pid_bag, \
			'brand_bag':  pack.data.brand_bag, \
	}), axis=1)
	return predict_gid_code

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
	argparser.add_argument('-E', '--ext', action='store_true', \
			help='append extensions to data and model path; use ".data.pkl" for data, and ".model.h5" for model.')

	argparser.add_argument('-d', '--data', metavar='<data_path>', required=True, \
			help='testing data path; load data from "[<dir>]<data_path>[.data.pkl]"')
	argparser.add_argument('-m', '--model', metavar='<model_path>', \
			help='model path; load model into "[<dir>]<model_path>[.model.h5]"')

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
	model_ext     = ''
	if args.ext:
		data_ext    = '.data.pkl'
		model_ext   = '.model.h5'

	data_file     = f'{result_root}{args.data}{data_ext}'
	model_file     = f'{result_root}{args.model}{model_ext}'

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
	print(f'num_test = {num_test}')

	# Load and apply model
	predict_model = model_load(model_file)
	predict_gid_code = model_predict(predict_model, pack)
	model_accuracy(predict_gid_code, pack.data.gid_code)
	model_accuracy(predict_gid_code, pack.data.gid_code, pack.data.rule == 'P_rule1', 'P_rule1')

	pass
