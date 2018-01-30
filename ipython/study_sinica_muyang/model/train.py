#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import os
import sys
import collections

import numpy

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


class ArgMax(keras.engine.topology.Layer):

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

	def build(self, input_shape):
		super().build(input_shape)

	def call(self, x):
		import keras.backend as K
		return K.argmax(x)

	def compute_output_shape(self, input_shape):
		return (input_shape[0], 1)


if __name__ == '__main__':

	emb_file     = f'data/embedding/prune_article_ws.dim300.emb.bin'
	model_path   = f'data/model'
	data_file    = f'{model_path}/data.h5'
	train_file   = f'{model_path}/train.json'
	predict_file = f'{model_path}/predict.json'
	weight_file  = f'{model_path}/weight.h5'

	# Load data
	data = Data.load(data_file)

	# Load word vectors
	keyed_vectors = KeyedVectors.load_word2vec_format(emb_file, binary=True)

	# Get sizes
	w2v_emb_size = keyed_vectors.vector_size
	num_vocab    = len(keyed_vectors.vocab)
	num_label    = max(data.p_id_code)+1
	print(f'num_vocab = {num_vocab}')
	print(f'num_label = {num_label}')

	# Prepare embeddings
	vocab_embedding = keyed_vectors.wv[keyed_vectors.index2word]
	# vocab_embedding[0] = 0
	label_embedding = numpy.identity(num_label, dtype='float32')

	# Split train and test
	train_data, test_data = data.train_test_split(test_size=0.25, random_state=0, shuffle=True)
	print(f'num_train = {train_data.size}')
	print(f'num_test  = {test_data.size}')

	# Count number of mentions and entities
	num_mention = len(train_data.p_id_code)
	counter     = collections.Counter(train_data.p_id_code)
	num_entity  = len(counter)
	train_data.text_weight = numpy.full((num_mention,), 1.0/num_mention, dtype='float32')
	train_data.desc_weight = numpy.asarray([counter[i]/num_entity for i in train_data.p_id_code], dtype='float32')

	# Define model
	cnn_win_size  = 5
	cnn_emb_size  = 100
	lstm_emb_size = 100
	emb_size      = 200

	pre_code   = keras.layers.Input(shape=(None,), dtype='int32', name='pre_code')
	post_code  = keras.layers.Input(shape=(None,), dtype='int32', name='post_code')
	desc_code  = keras.layers.Input(shape=(None,), dtype='int32', name='desc_code')
	label_code = keras.layers.Input(shape=(1,),    dtype='int32', name='label_code')

	text_weight = keras.layers.Input(shape=(1,), dtype='float32', name='text_weight')
	desc_weight = keras.layers.Input(shape=(1,), dtype='float32', name='desc_weight')

	word_emb_layer   = keras.layers.Embedding(num_vocab, w2v_emb_size, weights=[vocab_embedding], trainable=False, \
			name='word_emb')
	label_1hot_layer = keras.layers.Embedding(num_label, num_label,    weights=[label_embedding], trainable=False, \
			name='label_1hot')

	pre_code_emb   = word_emb_layer(pre_code)
	post_code_emb  = word_emb_layer(post_code)
	desc_code_emb  = word_emb_layer(desc_code)
	label_1hot = keras.layers.Flatten(name='label_1hot_flatten')(label_1hot_layer(label_code))

	pre_lstm    = keras.layers.LSTM(lstm_emb_size, go_backwards=False, name='pre_lstm')(pre_code_emb)
	post_lstm   = keras.layers.LSTM(lstm_emb_size, go_backwards=True,  name='post_lstm')(post_code_emb)
	text_concat = keras.layers.concatenate([pre_lstm, post_lstm], name='text_concat')
	text_emb    = keras.layers.Dense(emb_size, activation='tanh', name='text_emb')(text_concat)

	desc_cnn    = keras.layers.Conv1D(cnn_emb_size, cnn_win_size, name='desc_cnn')(desc_code_emb)
	desc_pool   = keras.layers.GlobalMaxPooling1D(name='desc_pool')(desc_cnn)
	desc_emb    = keras.layers.Dense(emb_size, activation='tanh', name='desc_emb')(desc_pool)

	entity_emb_layer = keras.layers.Dense(num_label, activation='softmax', use_bias=False, input_shape=(emb_size,), \
			name='entity_emb')

	text_softmax  = entity_emb_layer(text_emb)
	text_prob     = keras.layers.dot([label_1hot, text_softmax], axes=1, name='text_prob')
	text_log_prob = keras.layers.Lambda(keras.backend.log, name='text_log_prob')(text_prob)
	text_loss     = keras.layers.dot([text_log_prob, text_weight], axes=1, name='text_loss')

	desc_softmax  = entity_emb_layer(desc_emb)
	desc_prob     = keras.layers.dot([label_1hot, desc_softmax], axes=1, name='desc_prob')
	desc_log_prob = keras.layers.Lambda(keras.backend.log, name='desc_log_prob')(desc_prob)
	desc_loss     = keras.layers.dot([desc_log_prob, desc_weight], axes=1, name='desc_loss')

	target        = keras.layers.concatenate([text_loss, desc_loss], name='target')

	model = keras.models.Model( \
			inputs=[pre_code, post_code, desc_code, label_code, text_weight, desc_weight], \
			outputs=target)

	# Summarize the model
	print(f'\n\nTraining Model')
	model.summary()

	# Define predicting model
	text_max      = ArgMax(name='text_max')(text_softmax)
	predict_model = keras.models.Model(
			inputs=[pre_code, post_code], \
			outputs=[text_max] \
	)

	# Summarize predicting model
	print('\n\nPredicting Model')
	predict_model.summary()

	# Compile the model
	def custom_loss(y_true, y_pred):
		import keras.backend as K
		return -K.sum(y_pred)
	model.compile(optimizer='adam', loss=custom_loss)

	# Train the model
	model.fit( \
			{ \
					'pre_code':    train_data.pre_code, \
					'post_code':   train_data.post_code, \
					'desc_code':   train_data.desc_code, \
					'label_code':  train_data.p_id_code, \
					'text_weight': train_data.text_weight, \
					'desc_weight': train_data.desc_weight
			}, \
			train_data.p_id_code, epochs=10, batch_size=100)

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
