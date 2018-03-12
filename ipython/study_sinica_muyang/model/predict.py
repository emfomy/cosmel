#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import os
import sys

import numpy as np

import keras.backend
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
	predict_pid_code = np.argmax(predict_model.predict({
			'pre_code':  test_data.pre_code, \
			'post_code': test_data.post_code
	}), axis=1)
	return predict_pid_code

def model_accuracy(predict_pid_code, true_pid_code, mask=slice(None,None), name='all'):
	correct = (true_pid_code[mask] == predict_pid_code[mask])
	accuracy = correct.sum() / correct.size
	print(f'accuracy ({name}) = {accuracy} ({correct.sum()}/{correct.size})')

if __name__ == '__main__':

	assert len(sys.argv) == 2
	ver = sys.argv[1]

	data_root    = f'data/{ver}'
	model_root   = f'{data_root}/model'
	data_file    = f'{model_root}/data.h5'
	predict_file = f'{model_root}/predict.json'
	weight_file  = f'{model_root}/weight.h5'

	# Load data
	data = Data.load(data_file)
	train_data, test_data = data.train_test_split(test_size=0.3, random_state=0, shuffle=True)
	print(f'num_train = {train_data.size}')
	print(f'num_test  = {test_data.size}')

	# Load and apply model
	predict_model = model_load(predict_file, weight_file)
	predict_pid_code = model_predict(predict_model, test_data)
	model_accuracy(predict_pid_code, test_data.pid_code)
	model_accuracy(predict_pid_code, test_data.pid_code, test_data.rule == 'exact', 'exact')
	model_accuracy(predict_pid_code, test_data.pid_code, test_data.rule == '01a', '1a')
	model_accuracy(predict_pid_code, test_data.pid_code, test_data.rule == '01b', '1b')
	model_accuracy(predict_pid_code, test_data.pid_code, test_data.rule == '02a', '2a')
	model_accuracy(predict_pid_code, test_data.pid_code, test_data.rule == '03a', '3a')

	pass
