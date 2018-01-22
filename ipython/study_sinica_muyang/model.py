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
import sklearn.model_selection
import sklearn.utils

from gensim.models.keyedvectors import KeyedVectors

from styleme import *

def custom_loss(y_true, y_pred):
	return -keras.backend.mean(keras.backend.log(y_pred))

if __name__ == '__main__':

	repo_path    = 'data/repo'
	article_path = 'data/article/prune_article_ws'
	mention_path = 'data/mention/prune_article_ws_pid'
	# parts        = list(f'part-{x:05}' for x in range(10))
	parts        = ['']
	emb_file     = 'data/embedding/prune_article_ws.dim300.emb.bin'
	model_file   = 'data/model/model.h5'

	# Load word vectors
	keyed_vectors = KeyedVectors.load_word2vec_format(emb_file, binary=True)
	w2v_emb_size  = keyed_vectors.vector_size

	# Prepare tokenizer
	tokenizer = Tokenizer()
	tokenizer.fit_on_texts([' '.join(keyed_vectors.index2word)])
	num_vocab = len(tokenizer.word_index)+1
	print(f'num_vocab = {num_vocab}')

	# Load style repository and corpus
	repo   = Repo(repo_path)
	corpus = Corpus(article_path, mention_path, repo, parts=parts)

	# Remove mentions without PID and shuffle
	mention_data = sklearn.utils.shuffle([mention for mention in corpus.mention_set if mention.p_id.isdigit()])
	num_mention = len(mention_data)
	print(f'num_mention = {num_mention}')

	# Extract mentions
	max_num_sentences = 5

	mention_p_id_data         = [mention.p_id for mention in mention_data]
	mention_pre_content_data  = [ \
			' '.join(itertools.chain( \
					itertools.chain.from_iterable( \
							itertools.chain(s.txts, ['</s>']) \
							for s in mention.article[max(mention.s_id-max_num_sentences, 0):mention.s_id] \
					), \
					mention.sentence.txts[:mention.ending_idx] \
			)) for mention in mention_data \
	]
	mention_post_content_data  = [ \
			' '.join(itertools.chain( \
					mention.sentence.txts[:mention.ending_idx], \
					itertools.chain.from_iterable( \
							itertools.chain(['</s>'], s.txts) \
							for s in mention.article[mention.s_id+1:mention.s_id+1+max_num_sentences] \
					) \
			)) for mention in mention_data \
	]

	# for pid, pre, post in zip(mention_p_id_data, mention_pre_content_data, mention_post_content_data):
	#   print(pid, pre, post)

	# Integer encode the documents
	encoded_mention_pre_content_data  = tokenizer.texts_to_sequences(mention_pre_content_data)
	encoded_mention_post_content_data = tokenizer.texts_to_sequences(mention_post_content_data)

	# Pad documents
	padded_mention_pre_content_data  = pad_sequences(encoded_mention_pre_content_data, padding='pre')
	padded_mention_post_content_data = pad_sequences(encoded_mention_post_content_data, padding='post')

	# Prepare label encoder
	encoder = LabelEncoder()
	encoded_mention_p_id_data = encoder.fit_transform(mention_p_id_data)
	num_label = len(encoder.classes_)
	print(f'num_label = {num_label}')
	numpy.savetxt('data/tmp/label.txt', encoder.classes_, fmt='%s')

	# Split training and testing data
	padded_mention_pre_content_data_train, padded_mention_pre_content_data_test, \
		padded_mention_post_content_data_train, padded_mention_post_content_data_test, \
		encoded_mention_p_id_data_train, encoded_mention_p_id_data_test = \
			sklearn.model_selection.train_test_split( \
				padded_mention_pre_content_data, padded_mention_post_content_data, encoded_mention_p_id_data)
	print(f'num_train = {len(encoded_mention_p_id_data)}')
	print(f'num_test  = {len(encoded_mention_p_id_data_test)}')

	# Prepare embeddings
	vocab_embedding = keyed_vectors.wv[keyed_vectors.index2word]
	label_embedding = numpy.identity(num_label, dtype='float32')

	# Define model
	cnn_win_size  = 10
	cnn_emb_size  = 100
	lstm_emb_size = 100
	emb_size      = 200

	pre_code   = keras.layers.Input(shape=(None,), dtype='int32', name='pre')
	post_code  = keras.layers.Input(shape=(None,), dtype='int32', name='post')
	label_code = keras.layers.Input(shape=(1,),    dtype='int32', name='label')

	word_code_emb_l  = keras.layers.Embedding(num_vocab, w2v_emb_size, weights=[vocab_embedding], trainable=False, \
			name='word_code_emb')
	label_code_emb_l = keras.layers.Embedding(num_label, num_label,    weights=[label_embedding], trainable=False, \
			name='label_code_emb')

	pre_code_emb   = word_code_emb_l(pre_code)
	post_code_emb  = word_code_emb_l(post_code)
	label_code_emb = keras.layers.Flatten(name='label_code_flatten')(label_code_emb_l(label_code))

	pre_emb     = keras.layers.LSTM(lstm_emb_size, go_backwards=False, name='pre_emb')(pre_code_emb)
	post_emb    = keras.layers.LSTM(lstm_emb_size, go_backwards=True,  name='post_emb')(post_code_emb)
	text_concat = keras.layers.concatenate([pre_emb, post_emb], name='text_concat')
	text_emb    = keras.layers.Dense(emb_size, activation='tanh', name='text_emb')(text_concat)

	entity_emb_l = keras.layers.Dense(num_label, activation='softmax', use_bias=False, input_shape=(emb_size,), \
			name='entity_emb')

	text_prob   = entity_emb_l(text_emb)
	text_target = keras.layers.dot([text_prob, label_code_emb], axes=1, name='text_target')

	model = keras.models.Model( \
			inputs=[pre_code, post_code, label_code], \
			outputs=[text_target])

	# Summarize the model
	print(f'\n\n\nTraining Model')
	model.summary()

	# Define test model
	text_max   = keras.layers.Lambda(lambda x: keras.backend.argmax(x), name='text_max')(text_prob)
	test_model = keras.models.Model( \
			inputs=[pre_code, post_code], \
			outputs=[text_max])

	# Summarize test model
	print('\n\n\nTesting Model')
	test_model.summary()

	# Compile the model
	model.compile(optimizer='adam', loss=custom_loss)

	# Train the model
	model.fit({ \
			'pre':   padded_mention_pre_content_data_train, \
			'post':  padded_mention_post_content_data_train, \
			'label': encoded_mention_p_id_data_train}, \
			encoded_mention_p_id_data_train, epochs=10, batch_size=100)

	# Apply test model
	predicted_mention_p_id_data_test = test_model.predict({ \
			'pre':  padded_mention_pre_content_data_test, \
			'post': padded_mention_post_content_data_test})
	correct = (encoded_mention_p_id_data_test == predicted_mention_p_id_data_test)
	accuracy = correct.sum() / correct.size
	print(f'accuracy = {accuracy}')

	# Save model
	os.makedirs(os.path.dirname(model_file), exist_ok=True)
	model.save(model_file)

	pass
