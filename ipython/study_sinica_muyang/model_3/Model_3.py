#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = 'Chi-Yen Chen'
__email__ = 'jina199312@gmail.com'

import os
import numpy as np
import sys
import tensorflow as tf
# from keras.backend.tensorflow_backend import set_session

import keras.backend as K
import keras.models
import keras.layers

# from IPython import embed

from sklearn.model_selection import train_test_split

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences

from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MultiLabelBinarizer

from gensim.models.keyedvectors import KeyedVectors

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

config = tf.ConfigProto()
config.gpu_options.per_process_gpu_memory_fraction = 0.4
keras.backend.tensorflow_backend.set_session(tf.Session(config=config))


def custom_loss(y_true, y_pred):
	# return -keras.backend.mean(keras.backend.log(y_pred))
	return -K.mean(y_pred[:,-1] * K.log(K.sum(y_true * y_pred[:,:-1], axis=1)), axis=-1)



if __name__ == '__main__':

	use_pid = True

	assert len(sys.argv) > 1
	ver = sys.argv[1]

	target_ver   = f''
	if len(sys.argv)>2: target_ver = f'_{sys.argv[2]}' # gid_6.1
	data_root    = f'data/{ver}'
	parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = list(f'part-{x:05}' for x in range(127))

	repo_root      = f'{data_root}/repo'
	article_root   = f'{data_root}/article/pruned_article_role'
	mention_root   = f'{data_root}/mention/pruned_article{target_ver}'
	embedding_path = f'{data_root}/embedding/pruned_article.dim300.emb.bin'

	# Load word2vec
	word_vectors = KeyedVectors.load_word2vec_format(embedding_path, binary=True)
	W2V_EMB_SIZE = word_vectors.vector_size

	repo = Repo(repo_root)
	corpus = Corpus(article_root, mention_root, parts=parts)

	# Get mentions
	if use_pid:
		for mention in corpus.mention_set:
			if mention.pid:
				mention.set_gid(mention.pid)
			else:
				mention.set_gid('')
	mention_list = [m for m in corpus.mention_set if m.gid.isdigit()]
	mention_gid_list = [m.gid for m in mention_list]
	mention_num = len(mention_list)

	# load pre_content and post_cotent
	SENTENCE_NUM = 5
	pre_content = []
	post_cotent = []

	for mention in mention_list:
		pre = []
		for s in mention.article[max(mention.sid-SENTENCE_NUM, 0) : mention.sid]:
			pre += list(s.txts)
		pre += list(mention.sentence.txts[:mention.last_idx])

		post = list(mention.sentence.txts[mention.start_idx:])
		for s in mention.article[mention.sid+1 : mention.sid+SENTENCE_NUM+1]:
			post += list(s.txts)

		pre = ' '.join(a for a in pre)
		post = ' '.join(a for a in post)
		pre_content.append(pre)
		post_cotent.append(post)

	# load product descriptions
	rule = [mention.rule for mention in mention_list]

	# load product descriptions
	desc = [' '.join(repo.id_to_product[mention.gid].descr_ws.txts) for mention in mention_list]

	# load title
	title = [' '.join(mention.article[0].txts) for mention in mention_list]

	# load gid per document
	pid_doc   = [set(m.pid for m in mention.bundle if m.rule == 'P_rule1') for mention in mention_list]
	# load brand per document
	brand_doc = [set(repo.bname_to_brand[t[0]][0] \
					for t in itertools.chain.from_iterable(sentence.zip3 for sentence in mention.article) if t[2] == 'Brand' \
				) for mention in mention_list]

	# Prepare product label encoder
	p_encoder = LabelEncoder()
	p_encoder.fit(mention_gid_list + [p for s in pid_doc for p in s])
	gid_code = p_encoder.transform(mention_gid_list)
	label_num = len(p_encoder.classes_)
	print(f'label_num = {label_num}')

	# Prepare brand label encoder
	b_encoder = LabelEncoder()
	b_encoder.fit([b for s in brand_doc for b in s])
	brand_num = len(b_encoder.classes_)
	print(f'brand_num = {brand_num}')

	# Prepare product multi-binarizer
	p_multibinarizer = MultiLabelBinarizer(classes=p_encoder.classes_.tolist())
	p_multibinarizer.fit(pid_doc)

	# Prepare brand multi-binarizer
	b_multibinarizer = MultiLabelBinarizer(classes=b_encoder.classes_.tolist())
	b_multibinarizer.fit(brand_doc)

	# Encode bag of pid & bag of brand
	bag_of_pid   = p_multibinarizer.transform(pid_doc)
	bag_of_brand = b_multibinarizer.transform(brand_doc)

	# Get products
	product_list = [repo.id_to_product[p] for p in p_encoder.classes_]
	product_word_list = [' '.join(list(p.brand) + p.name_ws.txts) for p in product_list]
	product_word_list_len = [[1.0/len(p.split(' '))] for p in product_word_list]
	product_word_list_len_code = np.asarray(product_word_list_len, dtype='float32')

	# Prepare Tokenizer
	tokenizer = Tokenizer()
	tokenizer.fit_on_texts([' '.join(word_vectors.index2word[1:])])
	vocab_num = len(tokenizer.word_index)+1
	print('vocab_num = {}'.format(vocab_num))

	# Integer encode the documents
	encoded_pre_content     = tokenizer.texts_to_sequences(pre_content)
	encoded_post_content    = tokenizer.texts_to_sequences(post_cotent)
	encoded_title_content   = tokenizer.texts_to_sequences(title)
	encoded_desc_content    = tokenizer.texts_to_sequences(desc)
	encoded_product_content = tokenizer.texts_to_sequences(product_word_list)

	# Pad documents
	padded_pre_content     = pad_sequences(encoded_pre_content, padding='pre')
	padded_post_content    = pad_sequences(encoded_post_content, padding='post')
	padded_title_content   = pad_sequences(encoded_title_content, padding='post')
	padded_desc_content    = pad_sequences(encoded_desc_content, padding='post')
	padded_product_content = pad_sequences(encoded_product_content, padding='post')

	# Prepare embedding
	vocab_embedding = word_vectors.wv[word_vectors.index2word]
	vocab_embedding[0]=0
	# label_embedding = np.identity(label_num, dtype='float32')

	# Initialize entity embedding
	# product_init_embedding = np.zeros((len(p_encoder.classes_), word_vectors.vector_size))
	# for idx, p_id in enumerate(p_encoder.classes_):
	# 	p_init_emb = np.zeros((word_vectors.vector_size,))
	# 	product = repo.id_to_product[p_id]
	# 	# print(f'idx: {idx}, p_id: {p_id}, product: {product}')
	# 	count = 0
	# 	# get brand embedding
	# 	for b_word in product.brand:
	# 		b_word_emb = np.zeros((word_vectors.vector_size,))
	# 		if b_word in word_vectors.wv:
	# 			b_word_emb = word_vectors.wv[b_word]
	# 			count += 1
	# 		p_init_emb += b_word_emb
	# 	# get product word embeddding
	# 	for p_word in product.name_ws.txts:
	# 		p_word_emb = np.zeros((word_vectors.vector_size,))
	# 		if p_word in word_vectors.wv:
	# 			p_word_emb = word_vectors.wv[p_word]
	# 			count += 1
	# 		p_init_emb += p_word_emb
	# 	p_init_emb /= count
	# 	product_init_embedding[idx] = p_init_emb
	# product_init_embedding = product_init_embedding.T


	num_mention = len(gid_code)
	counter     = collections.Counter(gid_code)
	data_text_weight = np.full((num_mention,), 1., dtype='float32')
	data_desc_weight = np.asarray([1.0/counter[i] for i in gid_code], dtype='float32')
	gid_1hot = keras.utils.to_categorical(gid_code, num_classes=label_num)

	# Split Training/Testing data
	padded_title_content, padded_title_content_test, \
		padded_pre_content, padded_pre_content_test, \
		padded_post_content, padded_post_content_test, \
		padded_desc_content, padded_desc_content_test, \
		bag_of_pid, bag_of_pid_test, \
		bag_of_brand, bag_of_brand_test, \
		data_text_weight, data_text_weight_test, \
		data_desc_weight, data_desc_weight_test, \
		gid_1hot, gid_1hot_test, \
		gid_code, gid_code_test, \
		rule, rule_test, \
		 = train_test_split(padded_title_content, \
							padded_pre_content, \
							padded_post_content, \
							padded_desc_content, \
							bag_of_pid, \
							bag_of_brand, \
							data_text_weight, \
							data_desc_weight, \
							gid_1hot, \
							gid_code, \
							rule, \
							test_size=0.3, random_state=0, shuffle=True)

	# Define model
	LSTM_EMB_SIZE = 100
	print(f'lstm_emb_size   = {LSTM_EMB_SIZE}')
	CNN_WINDOW_SIZE = 5
	print(f'cnn_window_size = {CNN_WINDOW_SIZE}')
	CNN_EMB_SIZE = 100
	print(f'cnn_emb_size    = {CNN_EMB_SIZE}')
	ENTITY_EMB_SIZE = W2V_EMB_SIZE
	print(f'entity_emb_size = {ENTITY_EMB_SIZE}')

	pre_content_code   = keras.layers.Input(shape=(None,), dtype='int32', name='pre_content')
	post_content_code  = keras.layers.Input(shape=(None,), dtype='int32', name='post_content')
	title_content_code = keras.layers.Input(shape=(None,), dtype='int32', name='title_content')
	desc_content_code  = keras.layers.Input(shape=(None,), dtype='int32', name='desc_content')

	bag_of_pid_code   = keras.layers.Input(shape=(label_num,), dtype='float32', name='bag_of_pid')
	bag_of_brand_code = keras.layers.Input(shape=(brand_num,), dtype='float32', name='bag_of_brand')

	text_weight = keras.layers.Input(shape=(1,), dtype='float32', name='text_weight')
	desc_weight = keras.layers.Input(shape=(1,), dtype='float32', name='desc_weight')

	product_code = keras.layers.Input(tensor=K.constant(padded_product_content), name='product_content')


	text_code_layer  = keras.layers.Embedding(vocab_num, W2V_EMB_SIZE, weights=[vocab_embedding], trainable=True, name='text_code')

	title_code_emb = text_code_layer(title_content_code)
	pre_code_emb = text_code_layer(pre_content_code)
	post_code_emb = text_code_layer(post_content_code)
	desc_code_emb = text_code_layer(desc_content_code)

	product_code_emb = text_code_layer(product_code)

	product_word_list_len_const = K.constant(product_word_list_len_code)
	product_sum = keras.layers.Lambda(lambda x: K.sum(x, axis=1, keepdims=True), name='product_sum')(product_code_emb)
	product_avg = keras.layers.Lambda(lambda x: K.batch_dot(product_word_list_len_const, x, axes=[1, 1]), name='product_avg')(product_sum)

	title_content_lstm = keras.layers.Bidirectional(keras.layers.LSTM(LSTM_EMB_SIZE, go_backwards=False), name='title_content_lstm')(title_code_emb)
	pre_content_lstm = keras.layers.LSTM(LSTM_EMB_SIZE, go_backwards=False, name='pre_content_lstm')(pre_code_emb)
	post_content_lstm = keras.layers.LSTM(LSTM_EMB_SIZE, go_backwards=True, name='post_content_lstm')(post_code_emb)
	
	local_context_concat = keras.layers.concatenate([title_content_lstm, pre_content_lstm, post_content_lstm], name='local_context_concat')
	local_context_emb = keras.layers.Dense(W2V_EMB_SIZE, activation='relu', name='local_context_emb')(local_context_concat)

	doc_context_concat = keras.layers.concatenate([bag_of_pid_code, bag_of_brand_code], name='doc_context_concat')
	doc_context_emb = keras.layers.Dense(W2V_EMB_SIZE, activation='relu', name='doc_context_emb')(doc_context_concat)

	context_concat = keras.layers.concatenate([local_context_emb, doc_context_emb], name='context_concat')
	context_emb = keras.layers.Dense(W2V_EMB_SIZE, activation='relu', name='context_emb')(context_concat)

	desc_cnn  = keras.layers.Conv1D(CNN_EMB_SIZE, CNN_WINDOW_SIZE, name='desc_cnn')(desc_code_emb)
	desc_pool = keras.layers.GlobalMaxPooling1D(name='desc_pool')(desc_cnn)
	desc_emb  = keras.layers.Dense(W2V_EMB_SIZE, activation='relu', name='desc_emb')(desc_pool)

	entity_emb_layer = keras.layers.Lambda(lambda x: K.dot(x[0], K.permute_dimensions(x[1], (1, 0))), name='entity_emb')
	softmax_layer = keras.layers.Activation('softmax', name='softmax')

	context_softmax = softmax_layer(entity_emb_layer([context_emb, product_avg]))
	text_target  = keras.layers.concatenate([context_softmax, text_weight], name='text')

	desc_softmax = softmax_layer(entity_emb_layer([desc_emb, product_avg]))
	desc_target  = keras.layers.concatenate([desc_softmax, desc_weight], name='desc')

	model = keras.models.Model(\
			inputs=[title_content_code, \
					pre_content_code, \
					post_content_code, 
					desc_content_code, \
					bag_of_pid_code, \
					bag_of_brand_code, \
					text_weight, \
					desc_weight, \
					product_code], \
			outputs=[text_target, \
					desc_target])

	# Summarize the model
	print('\n\n\nTraining Model')
	model.summary()

	# Compile the model
	model.compile(optimizer='adam', loss=custom_loss)


	# Train the model
	input_data = { \
			'title_content': padded_title_content, \
			'pre_content':   padded_pre_content, \
			'post_content':  padded_post_content, \
			'desc_content': padded_desc_content, \
			'bag_of_pid': bag_of_pid, \
			'bag_of_brand': bag_of_brand, \
			'text_weight': data_text_weight, \
			'desc_weight': data_desc_weight, \
	}
	output_data = { \
			'text': gid_1hot, \
			'desc': gid_1hot, \
	}
	model.fit(input_data, output_data, epochs=20, batch_size=100)
	
	trained_word_emb = text_code_layer.get_weights()[0]
	np.savetxt('data/tmp/trained_word_emb.emb', trained_word_emb, fmt='%.4e')

	# Define Testing model
	# context_max = keras.layers.Lambda(keras.backend.argmax, name='context_max')(context_softmax)
	# test_model = keras.models.Model(\
	# 			inputs=[pre_content_code, \
	# 					post_content_code, 
	# 					title_content_code, \
	# 					desc_content_code, \
	# 					bag_of_pid_code, \
	# 					bag_of_brand_code], \
	# 			outputs=[content_max])
	test_model = keras.models.Model(\
				inputs=[title_content_code, \
						pre_content_code, \
						post_content_code, \
						bag_of_pid_code, \
						bag_of_brand_code, \
						product_code], \
				outputs=[context_softmax])

	# Testing model
	print('\n\n\nTesting Model')
	test_model.summary()

	gid_code_predict = np.argmax(test_model.predict({ \
		'title_content': padded_title_content_test, \
		'pre_content': padded_pre_content_test, \
		'post_content': padded_post_content_test, \
		'bag_of_pid': bag_of_pid_test, \
		'bag_of_brand': bag_of_brand_test, \
		}), axis=1)
	
	correct = (gid_code_test == gid_code_predict)
	accurarcy = correct.sum()/correct.size
	print(f'{correct.sum()}/{correct.size}')
	print(f'accurarcy = {accurarcy}')
	
	mask = (np.asarray(rule_test) == 'P_rule1')
	correct = (gid_code_test[mask] == gid_code_predict[mask])
	accurarcy = correct.sum()/correct.size
	print(f'{correct.sum()}/{correct.size}')
	print(f'accurarcy (P_rule1) = {accurarcy}')

	
	# # Get entity embedding
	# entity_weights = entity_emb_layer.get_weights()[0]
	# np.savetxt('data/tmp/entity_testing.emb', entity_weights, fmt='%.4e')


	pass