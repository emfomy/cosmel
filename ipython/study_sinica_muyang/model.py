#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import numpy

import keras.backend
import keras.layers
import keras.models
import keras.utils
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences

from sklearn.preprocessing import LabelEncoder
import sklearn.utils

from styleme import *

def custom_loss(y_true, y_pred):
	return -keras.backend.mean(keras.backend.log(y_pred))

if __name__ == '__main__':

	repo_path     = 'data/repo'
	article_path  = 'data/article/prune_article_ws'
	mention_path  = 'data/mention/prune_article_ws_pid'
	parts         = ['part-00000', 'part-00001']

	repo = Repo(repo_path)
	corpus = Corpus(article_path, mention_path, repo, parts=parts)

	# Remove mentions without PID and shuffle
	mention_list = sklearn.utils.shuffle([mention for mention in corpus.mention_set if mention.p_id.isdigit()])
	num_mention = len(mention_list)
	print('num_mention = {}'.format(num_mention))

	# Extract data
	max_num_sentences = 5

	mention_p_id_list         = [mention.p_id for mention in mention_list]
	mention_pre_content_list  = [ \
			' '.join(itertools.chain( \
					itertools.chain.from_iterable( \
							itertools.chain(s.txts, ['</s>']) \
							for s in mention.article[max(mention.s_id-max_num_sentences+1, 0):mention.s_id] \
					), \
					mention.sentence.txts[:mention.ending_idx] \
			)) for mention in mention_list \
	]
	mention_post_content_list  = [ \
			' '.join(itertools.chain( \
					mention.sentence.txts[:mention.ending_idx], \
					itertools.chain.from_iterable( \
							itertools.chain(['</s>'], s.txts) \
							for s in mention.article[mention.s_id+1:mention.s_id+max_num_sentences] \
					) \
			)) for mention in mention_list \
	]

	# for pid, pre, post in zip(mention_p_id_list, mention_pre_content_list, mention_post_content_list):
	# 	print(pid, pre, post)

	# Prepare tokenizer
	tokenizer = Tokenizer()
	tokenizer.fit_on_texts(mention_pre_content_list + mention_post_content_list)
	num_vocab = len(tokenizer.word_index)+1
	print('num_vocab = {}'.format(num_vocab))

	# Integer encode the documents
	encoded_mention_pre_content_list  = tokenizer.texts_to_sequences(mention_pre_content_list)
	encoded_mention_post_content_list = tokenizer.texts_to_sequences(mention_post_content_list)

	# Pad documents
	padded_mention_pre_content_list  = pad_sequences(encoded_mention_pre_content_list, padding='pre')
	padded_mention_post_content_list = pad_sequences(encoded_mention_post_content_list, padding='post')

	# Prepare label encoder
	encoder = LabelEncoder()
	encoded_mention_p_id_list = encoder.fit_transform(mention_p_id_list)
	num_label = len(encoder.classes_)
	print('num_label = {}'.format(num_label))
	numpy.savetxt('data/tmp/label.txt', encoder.classes_, fmt='%s')

	# Load embeddings
	vocab_embedding = numpy.identity(num_vocab, dtype='float32')
	label_embedding = numpy.identity(num_label, dtype='float32')

	# Define model
	cnn_win_size  = 10
	cnn_emb_size  = 100
	lstm_emb_size = 100
	emb_size      = 200

	pre_code   = keras.layers.Input(shape=(None,), dtype='int32', name='pre')
	post_code  = keras.layers.Input(shape=(None,), dtype='int32', name='post')
	label_code = keras.layers.Input(shape=(1,),    dtype='int32', name='label')

	pre_code_emb     = keras.layers.Embedding(num_vocab, num_vocab, weights=[vocab_embedding], trainable=False, \
			name='pre_code_emb')(pre_code)
	post_code_emb    = keras.layers.Embedding(num_vocab, num_vocab, weights=[vocab_embedding], trainable=False, \
			name='post_code_emb')(post_code)
	label_code_emb_0 = keras.layers.Embedding(num_label, num_label, weights=[label_embedding], trainable=False, \
			name='label_code_emb_0')(label_code)
	label_code_emb   = keras.layers.Flatten(name='label_code_emb')(label_code_emb_0)

	pre_emb     = keras.layers.LSTM(lstm_emb_size, go_backwards=False, name='pre_emb')(pre_code_emb)
	post_emb    = keras.layers.LSTM(lstm_emb_size, go_backwards=True,  name='post_emb')(post_code_emb)
	text_concat = keras.layers.concatenate([pre_emb, post_emb], name='text_concat')
	text_emb    = keras.layers.Dense(emb_size, activation='softmax', name='text_emb')(text_concat)

	entity_emb_l = keras.layers.Dense(num_label, activation='softmax', use_bias=False, input_shape=(emb_size,), \
			name='entity_emb')

	text_prob   = entity_emb_l(text_emb)
	text_target = keras.layers.dot([text_prob, label_code_emb], axes=1, name='text_target')

	model = keras.models.Model( \
			inputs=[pre_code, post_code, label_code], \
			outputs=[text_target])

	# Summarize the model
	model.summary()

	# Compile the model
	model.compile(optimizer='adam', loss=custom_loss)

	# Train the model
	model.fit({ \
			'pre':   padded_mention_pre_content_list, \
			'post':  padded_mention_post_content_list, \
			'label': encoded_mention_p_id_list}, \
			encoded_mention_p_id_list, epochs=2, batch_size=10)

	# Get entity embedding
	entity_weights = entity_emb_l.get_weights()[0]
	numpy.savetxt('data/tmp/entity.emb', entity_weights, fmt='%.4e')

	pass
