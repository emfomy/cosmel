#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import collections
import os
import re
import sys

import numpy as np

import keras.backend as K
import keras.layers
import keras.models
import keras.utils

sys.path.insert(0, os.path.abspath('.'))
from styleme import *
from data import DataPack


if __name__ == '__main__':

	# Parse arguments
	argparser = argparse.ArgumentParser(description='Train StyleMe model.')

	arggroup = argparser.add_mutually_exclusive_group()
	arggroup.add_argument('-v', '--ver', metavar='<ver>#<date>', \
			help='set <dir> as "result/<ver>_<date>"')
	arggroup.add_argument('-D', '--dir', metavar='<dir>', \
			help='prepend <dir> to data and model path')
	argparser.add_argument('-E', '--ext', action='store_true', \
			help='append extensions to data and model path; use ".data.pkl" for data, and ".model.h5" for model.')

	argparser.add_argument('-d', '--data', metavar='<data_path>', required=True, \
			help='training data path; load data from "[<dir>]<data_path>[.data.pkl]"')
	argparser.add_argument('-m', '--model', metavar='<model_path>', \
			help='output model path; output model into "[<dir>]<model_path>[.model.h5]"; default is "<data_path>" if "--ext" is set')
	argparser.add_argument('-p', '--pretrain', metavar='<pretrained_path>', \
			help='pretrained model path; load model from "[<dir>]<pretrained_path>[.model.h5]"')

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
		result_root = args.output

	data_ext      = ''
	model_ext     = ''
	if args.ext:
		data_ext    = '.data.pkl'
		model_ext   = '.model.h5'

	data_file     = f'{result_root}{args.data}{data_ext}'

	pretrain_file = ''
	if args.pretrain != None:
		pretrain_file = f'{result_root}{args.pretrain}{model_ext}'

	model_file    = f'{result_root}{args.data}{model_ext}'
	if args.model != None:
		model_file  = f'{result_root}{args.model}{model_ext}'
	assert model_file != data_file
	assert model_file != pretrain_file

	# Print arguments
	print()
	print(args)
	print()
	print(f'data_file     = {data_file}')
	print(f'model_file    = {model_file}')
	print(f'pretrain_file = {pretrain_file}')
	print()

	if args.check: exit()

	# Load data
	pack = DataPack.load(data_file)
	num_train = pack.data.gid_code.shape[0]
	print(f'num_train = {num_train}')

	# Load word vectors
	keyed_vectors = pack.info.keyed_vectors

	# Get sizes
	W2V_EMB_SIZE = keyed_vectors.vector_size
	num_vocab    = len(keyed_vectors.vocab)
	num_label    = pack.data.pid_bag.shape[1]
	num_brand    = pack.data.brand_bag.shape[1]
	print(f'num_vocab = {num_vocab}')
	print(f'num_label = {num_label}')
	print(f'num_brand = {num_brand}')

	# Prepare embeddings
	vocab_embedding = keyed_vectors[keyed_vectors.index2word]
	vocab_embedding[0] = 0

	# Prepare loss weights
	num_text = len(pack.data.gid_code)
	counter  = collections.Counter(pack.data.gid_code)
	num_desc = len(set(i for i in pack.data.gid_code if counter[i] != 0))
	pack.data.text_weight = np.full((num_text,), 1./num_text, dtype='float32')
	pack.data.desc_weight = np.asarray([1./counter[i]/num_desc for i in pack.data.gid_code], dtype='float32')
	print(f'num_text  = {num_text}')
	print(f'num_desc  = {num_desc}')

	# Prepare 1-hot for outputs
	pack.data.gid_1hot = keras.utils.to_categorical(pack.data.gid_code, num_classes=num_label)

	# Define model
	CNN_WIN_SIZE    = 5
	print(f'cnn_win_size    = {CNN_WIN_SIZE}')
	CNN_EMB_SIZE    = 100
	print(f'cnn_emb_size    = {CNN_EMB_SIZE}')
	LSTM_EMB_SIZE   = 100
	print(f'lstm_emb_size   = {LSTM_EMB_SIZE}')
	ENTITY_EMB_SIZE = W2V_EMB_SIZE
	print(f'entity_emb_size = {ENTITY_EMB_SIZE}')

	title_code  = keras.layers.Input(shape=(None,), dtype='int32', name='title_code')
	pre_code    = keras.layers.Input(shape=(None,), dtype='int32', name='pre_code')
	post_code   = keras.layers.Input(shape=(None,), dtype='int32', name='post_code')
	desc_code   = keras.layers.Input(shape=(None,), dtype='int32', name='desc_code')

	pid_bag     = keras.layers.Input(shape=(num_label,), dtype='float32', name='pid_bag')
	brand_bag   = keras.layers.Input(shape=(num_brand,), dtype='float32', name='brand_bag')

	text_weight = keras.layers.Input(shape=(1,), dtype='float32', name='text_weight')
	desc_weight = keras.layers.Input(shape=(1,), dtype='float32', name='desc_weight')

	word_emb_layer = keras.layers.Embedding(num_vocab, W2V_EMB_SIZE, weights=[vocab_embedding], trainable=False, \
			name='word_emb')

	title_code_emb = word_emb_layer(title_code)
	pre_code_emb   = word_emb_layer(pre_code)
	post_code_emb  = word_emb_layer(post_code)
	desc_code_emb  = word_emb_layer(desc_code)

	title_lstm   = keras.layers.Bidirectional(keras.layers.LSTM(LSTM_EMB_SIZE, go_backwards=False), \
				name='title_lstm')(title_code_emb)
	pre_lstm     = keras.layers.LSTM(LSTM_EMB_SIZE, go_backwards=False, name='pre_lstm')(pre_code_emb)
	post_lstm    = keras.layers.LSTM(LSTM_EMB_SIZE, go_backwards=True,  name='post_lstm')(post_code_emb)

	local_concat = keras.layers.concatenate([title_lstm, pre_lstm, post_lstm], name='local_concat')
	local_emb    = keras.layers.Dense(ENTITY_EMB_SIZE, activation='relu', name='local_emb')(local_concat)

	doc_concat   = keras.layers.concatenate([pid_bag, brand_bag], name='doc_concat')
	doc_emb      = keras.layers.Dense(ENTITY_EMB_SIZE, activation='relu', name='doc_emb')(doc_concat)

	text_concat  = keras.layers.concatenate([local_emb, doc_emb], name='text_concat')
	text_emb     = keras.layers.Dense(ENTITY_EMB_SIZE, activation='relu', name='text_emb')(text_concat)

	desc_cnn     = keras.layers.Conv1D(CNN_EMB_SIZE, CNN_WIN_SIZE, name='desc_cnn')(desc_code_emb)
	desc_pool    = keras.layers.GlobalMaxPooling1D(name='desc_pool')(desc_cnn)
	desc_emb     = keras.layers.Dense(ENTITY_EMB_SIZE, activation='relu', name='desc_emb')(desc_pool)

	entity_emb_layer = keras.layers.Dense(num_label, activation='softmax', use_bias=False, input_shape=(ENTITY_EMB_SIZE,), \
			name='entity_emb')

	text_softmax = entity_emb_layer(text_emb)
	text_target  = keras.layers.concatenate([text_softmax, text_weight], name='text')

	desc_softmax = entity_emb_layer(desc_emb)
	desc_target  = keras.layers.concatenate([desc_softmax, desc_weight], name='desc')

	if use_desc:
		train_model = keras.models.Model( \
				inputs=[ \
						title_code, \
						pre_code, \
						post_code, \
						desc_code, \
						pid_bag, \
						brand_bag, \
						text_weight, \
						desc_weight, \
				], \
				outputs=[ \
						text_target, \
						desc_target, \
				])
	else:
		train_model = keras.models.Model( \
				inputs=[ \
						title_code, \
						pre_code, \
						post_code, \
						pid_bag, \
						brand_bag, \
						text_weight, \
				], \
				outputs=[ \
						text_target, \
				])

	# Summarize the model
	train_model.summary()

	# Define predicting model
	predict_model = keras.models.Model(
			inputs=[title_code, pre_code, post_code, pid_bag, brand_bag], \
			outputs=[text_softmax] \
	)

	# Compile the model
	def custom_loss(y_true, y_pred):
		return -K.sum(y_pred[:,-1] * K.log(K.sum(y_true * y_pred[:,:-1], axis=1)), axis=-1)
	train_model.compile(optimizer='adam', loss=custom_loss)

	# Train the model
	input_data = { \
			'title_code':  pack.data.title_code, \
			'pre_code':    pack.data.pre_code, \
			'post_code':   pack.data.post_code, \
			'desc_code':   pack.data.desc_code, \
			'pid_bag':     pack.data.pid_bag, \
			'brand_bag':   pack.data.brand_bag, \
			'text_weight': pack.data.text_weight, \
			'desc_weight': pack.data.desc_weight, \
	}
	output_data = { \
			'text': pack.data.gid_1hot, \
			'name': pack.data.gid_1hot, \
			'desc': pack.data.gid_1hot, \
	}
	if not use_desc:
		del input_data['desc_code']
		del input_data['desc_weight']
		del output_data['name']
		del output_data['desc']

	# Train the model
	if pretrain_file:
		train_model.load_weights(pretrain_file)
		print(f'Loaded model weights from "{pretrain_file}"')
	train_model.fit(input_data, output_data, epochs=20, batch_size=1000)

	# Save models
	os.makedirs(os.path.dirname(train_file), exist_ok=True)
	train_model.save(train_file)
	print(f'Saved training model into "{train_file}"')

	os.makedirs(os.path.dirname(predict_file), exist_ok=True)
	predict_model.save(predict_file)
	print(f'Saved predicting model into "{predict_file}"')

	pass
