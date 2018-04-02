#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


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

	if len(sys.argv) <= 1:
		print(f'Usage: {sys.argv[0]} <ver> [mention_suffix] [model_suffix] [test_data_suffix]\n')

	assert len(sys.argv) > 1
	ver = sys.argv[1]

	target_ver   = f''
	if len(sys.argv) > 2: target_ver = f'_{sys.argv[2]}'
	train_ver    = f''
	if len(sys.argv) > 3: train_ver  = f'.{sys.argv[3]}'
	test_ver     = train_ver
	if len(sys.argv) > 4: test_ver   = f'.{sys.argv[4]}'

	data_root    = f'data/{ver}'
	model_root   = f'{data_root}/model'
	data_file    = f'{model_root}/pruned_article{target_ver}.data{test_ver}.test.pkl'
	model_file   = f'{model_root}/pruned_article{target_ver}.predict{train_ver}.h5'

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
