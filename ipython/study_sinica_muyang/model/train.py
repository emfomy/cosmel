#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
   Mu Yang <emfomy@gmail.com>
"""

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

os.chdir(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.abspath('.'))
from styleme import *
from data import Data


def custom_loss(y_true, y_pred):
	import keras.backend as K
	return -y_pred[-1] * K.log(K.sum(y_true * y_pred[:-1]))


if __name__ == '__main__':

	use_model3 = False
	use_desc   = True

	emb_file     = f'data/embedding/prune_article_ws.dim300.emb.bin'
	model_root   = f'data/model'
	data_file    = f'{model_root}/data.h5'
	train_file   = f'{model_root}/train.json'
	predict_file = f'{model_root}/predict.json'
	weight_file  = f'{model_root}/weight.h5'

	# Load data
	data = Data.load(data_file)

	# Load initial product embedding
	if use_model3:
		init_file = f'{model_root}/init.h5'
		h5f = h5py.File(init_file, 'r')
		product_init_embedding = h5f['product_init_embedding'][:]
		h5f.close()

	# Load word vectors
	keyed_vectors = KeyedVectors.load_word2vec_format(emb_file, binary=True)

	# Get sizes
	W2V_EMB_SIZE = keyed_vectors.vector_size
	num_vocab    = len(keyed_vectors.vocab)
	num_label    = max(data.p_id_code)+1
	print(f'num_vocab = {num_vocab}')
	print(f'num_label = {num_label}')

	# Prepare embeddings
	vocab_embedding = keyed_vectors.wv[keyed_vectors.index2word]
	vocab_embedding[0] = 0

	# Split train and test
	train_data, test_data = data.train_test_split(test_size=0.3, random_state=0, shuffle=True)
	print(f'num_train = {train_data.size}')
	print(f'num_test  = {test_data.size}')

	# Prepare loss weights
	num_mention = len(train_data.p_id_code)
	counter     = collections.Counter(train_data.p_id_code)
	train_data.text_weight = np.full((num_mention,), 1., dtype='float32')
	train_data.desc_weight = np.asarray([1/counter[i] for i in train_data.p_id_code], dtype='float32')

	# Prepare 1-hot for outputs
	train_data.p_id_1hot   = keras.utils.to_categorical(train_data.p_id_code, num_classes=num_label)

	# Define model
	CNN_WIN_SIZE    = 5
	CNN_EMB_SIZE    = 100
	LSTM_EMB_SIZE   = 100
	ENTITY_EMB_SIZE = W2V_EMB_SIZE
	print(f'cnn_win_size    = {CNN_WIN_SIZE}')
	print(f'cnn_emb_size    = {CNN_EMB_SIZE}')
	print(f'lstm_emb_size   = {LSTM_EMB_SIZE}')
	print(f'entity_emb_size = {ENTITY_EMB_SIZE}')

	pre_code  = keras.layers.Input(shape=(None,), dtype='int32', name='pre_code')
	post_code = keras.layers.Input(shape=(None,), dtype='int32', name='post_code')
	desc_code = keras.layers.Input(shape=(None,), dtype='int32', name='desc_code')

	text_weight = keras.layers.Input(shape=(1,), dtype='float32', name='text_weight')
	desc_weight = keras.layers.Input(shape=(1,), dtype='float32', name='desc_weight')

	word_emb_layer   = keras.layers.Embedding(num_vocab, W2V_EMB_SIZE, weights=[vocab_embedding], trainable=False, \
			name='word_emb')

	pre_code_emb  = word_emb_layer(pre_code)
	post_code_emb = word_emb_layer(post_code)
	desc_code_emb = word_emb_layer(desc_code)

	pre_lstm    = keras.layers.LSTM(LSTM_EMB_SIZE, go_backwards=False, name='pre_lstm')(pre_code_emb)
	post_lstm   = keras.layers.LSTM(LSTM_EMB_SIZE, go_backwards=True,  name='post_lstm')(post_code_emb)
	text_concat = keras.layers.concatenate([pre_lstm, post_lstm], name='text_concat')
	text_emb    = keras.layers.Dense(ENTITY_EMB_SIZE, activation='tanh', name='text_emb')(text_concat)

	desc_cnn  = keras.layers.Conv1D(CNN_EMB_SIZE, CNN_WIN_SIZE, name='desc_cnn')(desc_code_emb)
	desc_pool = keras.layers.GlobalMaxPooling1D(name='desc_pool')(desc_cnn)
	desc_emb  = keras.layers.Dense(ENTITY_EMB_SIZE, activation='tanh', name='desc_emb')(desc_pool)

	if not use_model3:
		entity_emb_layer = keras.layers.Dense(num_label, activation='softmax', use_bias=False, input_shape=(ENTITY_EMB_SIZE,), \
				name='entity_emb')
	else:
		entity_emb_layer = keras.layers.Dense(num_label, activation='softmax', use_bias=False, input_shape=(ENTITY_EMB_SIZE,), \
				weights=[product_init_embedding], name='entity_emb')

	text_softmax = entity_emb_layer(text_emb)
	text_target  = keras.layers.concatenate([text_softmax, text_weight], name='text')

	desc_softmax = entity_emb_layer(desc_emb)
	desc_target  = keras.layers.concatenate([desc_softmax, desc_weight], name='desc')

	if use_desc:
		model = keras.models.Model( \
				inputs=[ \
						pre_code, \
						post_code, \
						desc_code, \
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
						pre_code, \
						post_code, \
						text_weight, \
				], \
				outputs=[ \
						text_target, \
				])

	# Summarize the model
	model.summary()

	# Define predicting model
	predict_model = keras.models.Model(
			inputs=[pre_code, post_code], \
			outputs=[text_softmax] \
	)

	# Compile the model
	def custom_loss(y_true, y_pred):
		import keras.backend as K
		return -K.mean(y_pred[:,-1] * K.log(K.sum(y_true * y_pred[:,:-1], axis=1)), axis=-1)
	model.compile(optimizer='adam', loss=custom_loss)

	# Train the model
	input_data = { \
			'pre_code':    train_data.pre_code, \
			'post_code':   train_data.post_code, \
			'desc_code':   train_data.desc_code, \
			'text_weight': train_data.text_weight, \
			'desc_weight': train_data.desc_weight, \
	}
	output_data = { \
				'text': train_data.p_id_1hot, \
				'desc': train_data.p_id_1hot, \
	}
	if not use_desc:
		del input_data['desc_code']
		del input_data['desc_weight']
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
