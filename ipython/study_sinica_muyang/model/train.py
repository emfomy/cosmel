#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import collections
import h5py
import os
import sys

import numpy as np

import keras.backend
import keras.layers
import keras.models
import keras.utils
import keras.engine.topology

from gensim.models.keyedvectors import KeyedVectors

sys.path.insert(0, os.path.abspath('.'))
from styleme import *
from data import Data


if __name__ == '__main__':

	assert len(sys.argv) > 1
	ver = sys.argv[1]

	use_desc     = True

	target_ver   = f''
	if len(sys.argv) > 2: target_ver = f'_{sys.argv[2]}'
	data_root    = f'data/{ver}'
	emb_file     = f'{data_root}/embedding/pruned_article.dim300.emb.bin'
	model_root   = f'{data_root}/model'
	data_file    = f'{model_root}/data{target_ver}.h5'
	train_file   = f'{model_root}/train{target_ver}.json'
	predict_file = f'{model_root}/predict{target_ver}.json'
	weight_file  = f'{model_root}/weight{target_ver}.h5'

	# Load data
	data = Data.load(data_file)

	# Load word vectors
	keyed_vectors = KeyedVectors.load_word2vec_format(emb_file, binary=True)

	# Get sizes
	W2V_EMB_SIZE = keyed_vectors.vector_size
	num_vocab    = len(keyed_vectors.vocab)
	num_label    = data.pid_bag.shape[1]
	num_brand    = data.brand_bag.shape[1]
	print(f'num_vocab = {num_vocab}')
	print(f'num_label = {num_label}')
	print(f'num_brand = {num_brand}')

	# Prepare embeddings
	vocab_embedding = keyed_vectors.wv[keyed_vectors.index2word]
	vocab_embedding[0] = 0

	# Split train and test
	train_data, test_data = data.train_test_split(test_size=0.3, random_state=0, shuffle=True)
	print(f'num_train = {train_data.size}')
	print(f'num_test  = {test_data.size}')

	# Prepare loss weights
	num_mention = len(train_data.pid_code)
	counter     = collections.Counter(train_data.pid_code)
	train_data.text_weight = np.full((num_mention,), 1., dtype='float32')
	train_data.desc_weight = np.asarray([1/counter[i] for i in train_data.pid_code], dtype='float32')

	# Prepare 1-hot for outputs
	train_data.pid_1hot   = keras.utils.to_categorical(train_data.pid_code, num_classes=num_label)

	# Define model
	CNN_WIN_SIZE    = 5
	print(f'cnn_win_size    = {CNN_WIN_SIZE}')
	CNN_EMB_SIZE    = 100
	print(f'cnn_emb_size    = {CNN_EMB_SIZE}')
	LSTM_EMB_SIZE   = 100
	print(f'lstm_emb_size   = {LSTM_EMB_SIZE}')
	ENTITY_EMB_SIZE = W2V_EMB_SIZE
	print(f'entity_emb_size = {ENTITY_EMB_SIZE}')

	title_code = keras.layers.Input(shape=(None,), dtype='int32', name='title_code')
	pre_code   = keras.layers.Input(shape=(None,), dtype='int32', name='pre_code')
	post_code  = keras.layers.Input(shape=(None,), dtype='int32', name='post_code')
	desc_code  = keras.layers.Input(shape=(None,), dtype='int32', name='desc_code')

	pid_bag    = keras.layers.Input(shape=(num_label,), dtype='float32', name='pid_bag')
	brand_bag  = keras.layers.Input(shape=(num_brand,), dtype='float32', name='brand_bag')

	text_weight = keras.layers.Input(shape=(1,), dtype='float32', name='text_weight')
	desc_weight = keras.layers.Input(shape=(1,), dtype='float32', name='desc_weight')

	word_emb_layer = keras.layers.Embedding(num_vocab, W2V_EMB_SIZE, weights=[vocab_embedding], trainable=False, \
			name='word_emb')

	title_code_emb = word_emb_layer(title_code)
	pre_code_emb   = word_emb_layer(pre_code)
	post_code_emb  = word_emb_layer(post_code)
	desc_code_emb  = word_emb_layer(desc_code)

	title_lstm   = keras.layers.LSTM(LSTM_EMB_SIZE,   go_backwards=False, name='title_lstm')(pre_code_emb)
	pre_lstm     = keras.layers.LSTM(LSTM_EMB_SIZE,   go_backwards=False, name='pre_lstm')(pre_code_emb)
	post_lstm    = keras.layers.LSTM(LSTM_EMB_SIZE,   go_backwards=True,  name='post_lstm')(post_code_emb)

	local_concat = keras.layers.concatenate([title_lstm, pre_lstm, post_lstm], name='local_concat')
	local_emb    = keras.layers.Dense(ENTITY_EMB_SIZE, activation='relu', name='local_emb')(local_concat)

	doc_concat   = keras.layers.concatenate([pid_bag, brand_bag], name='doc_concat')
	doc_emb      = keras.layers.Dense(ENTITY_EMB_SIZE, activation='relu', name='doc_emb')(doc_concat)

	text_concat  = keras.layers.concatenate([local_emb, doc_emb], name='text_concat')
	text_emb     = keras.layers.Dense(ENTITY_EMB_SIZE, activation='relu', name='text_emb')(text_concat)

	desc_cnn  = keras.layers.Conv1D(CNN_EMB_SIZE, CNN_WIN_SIZE, name='desc_cnn')(desc_code_emb)
	desc_pool = keras.layers.GlobalMaxPooling1D(name='desc_pool')(desc_cnn)
	desc_emb  = keras.layers.Dense(ENTITY_EMB_SIZE, activation='relu', name='desc_emb')(desc_pool)

	entity_emb_layer = keras.layers.Dense(num_label, activation='softmax', use_bias=False, input_shape=(ENTITY_EMB_SIZE,), \
			name='entity_emb')

	text_softmax = entity_emb_layer(text_emb)
	text_target  = keras.layers.concatenate([text_softmax, text_weight], name='text')

	desc_softmax = entity_emb_layer(desc_emb)
	desc_target  = keras.layers.concatenate([desc_softmax, desc_weight], name='desc')

	if use_desc:
		model = keras.models.Model( \
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
		model = keras.models.Model( \
				inputs=[ \
						title_code, \
						pre_code, \
						post_code, \
						desc_code, \
						pid_bag, \
						brand_bag, \
						text_weight, \
				], \
				outputs=[ \
						text_target, \
				])

	# Summarize the model
	model.summary()

	# Define predicting model
	predict_model = keras.models.Model(
			inputs=[title_code, pre_code, post_code, pid_bag, brand_bag], \
			outputs=[text_softmax] \
	)

	# Compile the model
	def custom_loss(y_true, y_pred):
		import keras.backend as K
		return -K.mean(y_pred[:,-1] * K.log(K.sum(y_true * y_pred[:,:-1], axis=1)), axis=-1)
	model.compile(optimizer='adam', loss=custom_loss)

	# Train the model
	input_data = { \
			'title_code':  train_data.title_code, \
			'pre_code':    train_data.pre_code, \
			'post_code':   train_data.post_code, \
			'desc_code':   train_data.desc_code, \
			'pid_bag':     train_data.pid_bag, \
			'brand_bag':   train_data.brand_bag, \
			'text_weight': train_data.text_weight, \
			'desc_weight': train_data.desc_weight, \
	}
	output_data = { \
			'text': train_data.pid_1hot, \
			'name': train_data.pid_1hot, \
			'desc': train_data.pid_1hot, \
	}
	if not use_desc:
		del input_data['desc_code']
		del input_data['desc_weight']
		del output_data['name']
		del output_data['desc']

	model.fit(input_data, output_data, epochs=20, batch_size=1000)

	# Save models
	os.makedirs(os.path.dirname(train_file), exist_ok=True)
	with open(train_file, 'w') as fout:
		fout.write(model.to_json())
		print(f'Saved training model into "{train_file}"')

	os.makedirs(os.path.dirname(predict_file), exist_ok=True)
	with open(predict_file, 'w') as fout:
		fout.write(predict_model.to_json())
		print(f'Saved predicting model into "{predict_file}"')

	os.makedirs(os.path.dirname(weight_file), exist_ok=True)
	predict_model.save_weights(weight_file)
	print(f'Saved model weights into "{weight_file}"')

	pass
