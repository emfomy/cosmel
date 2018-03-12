#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import h5py
import itertools
import os
import sys

import numpy as np

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences

from sklearn.preprocessing import LabelEncoder
import sklearn.model_selection

from gensim.models.keyedvectors import KeyedVectors

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

class Data:

	_attr = ['pid_code', 'pre_code', 'post_code', 'desc_code', 'aid', 'sid', 'idx', 'rule', 'pid']

	def __getitem__(self, key):
		data = Data()
		for attr in Data._attr:
			setattr(data, attr, getattr(self, attr)[key])
		return data

	@property
	def size(self):
		return len(self.pid_code)

	@staticmethod
	def load(file):
		data = Data()
		h5f = h5py.File(file, 'r')
		for attr in Data._attr:
			setattr(data, attr, h5f[attr][:])
			if getattr(data, attr).dtype.kind == 'S':
				setattr(data, attr, np.array(getattr(data, attr), dtype='str'))
		h5f.close()
		print(f'Loaded data from "{file}"')
		return data

	def train_test_split(self, *args, **kwargs):
		train_data = Data()
		test_data  = Data()
		splitting  = sklearn.model_selection.train_test_split(*(getattr(self, attr) for attr in Data._attr), *args, **kwargs)
		for i, attr in enumerate(Data._attr):
			setattr(train_data, attr, splitting[2*i])
			setattr(test_data,  attr, splitting[2*i+1])
		return train_data, test_data

class RawData(Data):

	max_num_sentences = 5

	def __init__(self, repo, mention_list):
		self.aid = [mention.aid for mention in mention_list]
		self.sid = [mention.sid for mention in mention_list]
		self.mid = [mention.mid for mention in mention_list]
		self.rule = [mention.rule for mention in mention_list]
		self.pid = [mention.pid for mention in mention_list]

		self.pre  = [ \
				' '.join(itertools.chain( \
						itertools.chain.from_iterable( \
								s.txts for s in mention.article[max(mention.sid-RawData.max_num_sentences, 0):mention.sid] \
						), \
						mention.sentence.txts[:mention.end_idx] \
				)) for mention in mention_list \
		]
		self.post = [ \
				' '.join(itertools.chain( \
						mention.sentence.txts[mention.start_idx:], \
						itertools.chain.from_iterable( \
								s.txts for s in mention.article[mention.sid+1:mention.sid+1+RawData.max_num_sentences] \
						) \
				)) for mention in mention_list \
		]
		self.desc  = [' '.join(repo.id_to_product[mention.pid].descr_ws.txts) for mention in mention_list]

	def encode(self, tokenizer, encoder):
		self.pid_code  = encoder.transform(self.pid)
		self.pre_code   = pad_sequences(tokenizer.texts_to_sequences(self.pre),  padding='pre')
		self.post_code  = pad_sequences(tokenizer.texts_to_sequences(self.post), padding='post')
		self.desc_code  = pad_sequences(tokenizer.texts_to_sequences(self.desc), padding='post')
		self.classes    = encoder.classes_

	def save(self, file, comment=''):
		os.makedirs(os.path.dirname(file), exist_ok=True)
		h5f = h5py.File(file, 'w')
		h5f.create_dataset('comment',   data=comment)
		h5f.create_dataset('pid_code', data=self.pid_code)
		h5f.create_dataset('pre_code',  data=self.pre_code)
		h5f.create_dataset('post_code', data=self.post_code)
		h5f.create_dataset('desc_code', data=self.desc_code)
		h5f.create_dataset('aid',      data=[x.encode("ascii") for x in self.aid])
		h5f.create_dataset('sid',      data=self.sid, dtype='int32')
		h5f.create_dataset('mid',      data=self.mid,  dtype='int32')
		h5f.create_dataset('rule',      data=[x.encode("ascii") for x in self.rule])
		h5f.create_dataset('pid',      data=[x.encode("ascii") for x in self.pid])
		h5f.create_dataset('classes',   data=[x.encode("ascii") for x in self.classes])
		h5f.close()
		print(f'Saved data into "{file}"')

if __name__ == '__main__':

	assert len(sys.argv) == 2
	ver = sys.argv[1]

	data_root    = f'data/{ver}'
	repo_root    = f'{data_root}/repo'
	article_root = f'{data_root}/article/pruned_article_ws'
	mention_root = f'{data_root}/mention/pruned_article_ws_pid'
	model_root   = f'{data_root}/model'
	parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	emb_file     = f'{data_root}/embedding/pruned_article_ws.dim300.emb.bin'
	data_file    = f'{model_root}/data.h5'
	init_file    = f'{model_root}/init.h5'

	# Load word vectors
	keyed_vectors = KeyedVectors.load_word2vec_format(emb_file, binary=True)

	# Prepare tokenizer
	tokenizer = Tokenizer()
	tokenizer.fit_on_texts([' '.join(keyed_vectors.index2word[1:])])
	num_vocab = len(tokenizer.word_index)+1
	print(f'num_vocab = {num_vocab}')

	# Load StyleMe repository and corpus
	repo   = Repo(repo_root)
	corpus = Corpus(article_root, mention_root, repo, parts=parts)

	# Extract mentions with PID
	mention_list = [mention for mention in corpus.mention_set if mention.pid.isdigit()]
	num_mention = len(mention_list)
	print(f'num_mention = {num_mention}')

	# Extract mention data
	data = RawData(repo, mention_list)

	# Prepare label encoder
	encoder = LabelEncoder()
	encoder.fit(data.pid)
	num_label = len(encoder.classes_)
	print(f'num_label = {num_label}')

	# Integer encode the documents and the labels
	data.encode(tokenizer, encoder)

	# Save data
	comment = \
			f'article_root={article_root}\n' \
			f'mention_root={mention_root}\n' \
			f'emb_file={emb_file}\n' \
			f'max_num_sentences={RawData.max_num_sentences}'
	data.save(data_file, comment)

	# Initialize entity embedding
	product_init_embedding = np.zeros((num_label, keyed_vectors.vector_size))
	for idx, pid in enumerate(encoder.classes_):
		product = repo.id_to_product[pid]
		product_init_embedding[idx] = np.mean(keyed_vectors.wv[
			[word for word in itertools.chain(product.brand, product.name_ws.txts) if word in keyed_vectors.wv]
		], axis=0)
	product_init_embedding = product_init_embedding.T

	h5f = h5py.File(init_file, 'w')
	h5f.create_dataset('product_init_embedding', data=product_init_embedding)
	h5f.close()
	print(f'Saved initial embedding into "{init_file}"')

	pass
