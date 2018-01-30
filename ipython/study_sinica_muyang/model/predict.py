#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import os
import sys

import numpy

import keras.backend
import keras.layers
import keras.models
import keras.utils

from gensim.models.keyedvectors import KeyedVectors

os.chdir(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.abspath('.'))
from styleme import *
from data import Data
from train import ArgMax

if __name__ == '__main__':

	model_root   = f'data/model'
	data_file    = f'{model_root}/data.h5'
	predict_file = f'{model_root}/predict.json'
	weight_file  = f'{model_root}/weight.h5'

	# Load data
	data = Data.load(data_file)
	train_data, test_data = data.train_test_split(test_size=0.25, random_state=0, shuffle=True)
	print(f'num_train = {train_data.size}')
	print(f'num_test  = {test_data.size}')

	# Load model
	with open(predict_file) as fin:
		predict_model = keras.models.model_from_json(fin.read(), custom_objects={"ArgMax": ArgMax})
		print(f'Loaded predicting model from "{predict_file}"')
	predict_model.load_weights(weight_file)
	print(f'Loaded model weights from "{weight_file}"')
	predict_model.summary()

	# Apply model
	predict_p_id_code = predict_model.predict({
			'pre_code':  test_data.pre_code, \
			'post_code': test_data.post_code
	})
	correct = (test_data.p_id_code == predict_p_id_code)
	accuracy = correct.sum() / correct.size
	print(f'accuracy = {accuracy}')

	pass
