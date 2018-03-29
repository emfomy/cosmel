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
from data import Data

def model_load(predict_file, weight_file):
	with open(predict_file) as fin:
		predict_model = keras.models.model_from_json(fin.read())
		print(f'Loaded predicting model from "{predict_file}"')
	predict_model.load_weights(weight_file)
	print(f'Loaded model weights from "{weight_file}"')
	predict_model.summary()
	return predict_model

def model_predict(predict_model, test_data):
	predict_gid_code = np.argmax(predict_model.predict({
			'title_code': test_data.title_code, \
			'pre_code':   test_data.pre_code, \
			'post_code':  test_data.post_code, \
			'pid_bag':    test_data.pid_bag, \
			'brand_bag':  test_data.brand_bag, \
	}), axis=1)
	return predict_gid_code

def model_accuracy(predict_gid_code, true_gid_code, mask=slice(None,None), name='all'):
	correct = (true_gid_code[mask] == predict_gid_code[mask])
	accuracy = correct.sum() / correct.size
	print(f'accuracy ({name}) = {accuracy} ({correct.sum()}/{correct.size})')

if __name__ == '__main__':

	assert len(sys.argv) > 1
	ver = sys.argv[1]

	target_ver   = f''
	if len(sys.argv) > 2: target_ver = f'_{sys.argv[2]}'
	data_ver     = target_ver
	if len(sys.argv) > 3: data_ver = f'_{sys.argv[3]}'
	data_root    = f'data/{ver}'
	model_root   = f'{data_root}/model'
	data_file    = f'{model_root}/data{data_ver}.h5'
	predict_file = f'{model_root}/predict{target_ver}.json'
	weight_file  = f'{model_root}/weight{target_ver}.h5'

	# Load data
	data = Data.load(data_file)
	train_data, test_data = data.train_test_split(test_size=0.3, random_state=0, shuffle=True)
	print(f'num_train = {train_data.size}')
	print(f'num_test  = {test_data.size}')

	# Load and apply model
	predict_model = model_load(predict_file, weight_file)
	predict_gid_code = model_predict(predict_model, test_data)
	model_accuracy(predict_gid_code, test_data.gid_code)
	model_accuracy(predict_gid_code, test_data.gid_code, test_data.rule == 'P_rule1', 'P_rule1')

	pass
