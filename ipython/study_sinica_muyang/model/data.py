#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import h5py
import os
import sys

import numpy

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences

from sklearn.preprocessing import LabelEncoder
import sklearn.model_selection

from gensim.models.keyedvectors import KeyedVectors

os.chdir(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.abspath('.'))
from styleme import *

class Data:

	_attr = ['p_id_code', 'pre_code', 'post_code', 'desc_code', 'a_id', 's_id', 'idx', 'rule', 'p_id']

	@property
	def size(self):
		return len(self.p_id_code)

	@staticmethod
	def load(file):
		data = Data()
		os.makedirs(os.path.dirname(file), exist_ok=True)
		h5f = h5py.File(file, 'r')
		for attr in Data._attr:
			setattr(data, attr, h5f[attr][:])
			if getattr(data, attr).dtype.kind == 'S':
				setattr(data, attr, numpy.array(getattr(data, attr), dtype='str'))
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
		self.a_id = [mention.a_id for mention in mention_list]
		self.s_id = [mention.s_id for mention in mention_list]
		self.idx  = [mention.beginning_idx for mention in mention_list]
		self.rule = [mention.rule for mention in mention_list]
		self.p_id = [mention.p_id for mention in mention_list]

		self.pre  = [ \
				' '.join(itertools.chain( \
						itertools.chain.from_iterable( \
								s.txts for s in mention.article[max(mention.s_id-RawData.max_num_sentences, 0):mention.s_id] \
						), \
						mention.sentence.txts[:mention.ending_idx] \
				)) for mention in mention_list \
		]
		self.post = [ \
				' '.join(itertools.chain( \
						mention.sentence.txts[mention.beginning_idx:], \
						itertools.chain.from_iterable( \
								s.txts for s in mention.article[mention.s_id+1:mention.s_id+1+RawData.max_num_sentences] \
						) \
				)) for mention in mention_list \
		]
		self.desc = [' '.join(repo.id_to_product[mention.p_id].descr_ws.txts) for mention in mention_list]

	def encode(self, tokenizer, encoder):
		self.p_id_code = encoder.transform(self.p_id)
		self.pre_code  = pad_sequences(tokenizer.texts_to_sequences(self.pre),  padding='pre')
		self.post_code = pad_sequences(tokenizer.texts_to_sequences(self.post), padding='post')
		self.desc_code = pad_sequences(tokenizer.texts_to_sequences(self.desc), padding='post')
		self.classes   = encoder.classes_

	def save(self, file, comment=''):
		os.makedirs(os.path.dirname(file), exist_ok=True)
		h5f = h5py.File(file, 'w')
		h5f.create_dataset('comment',   data=comment)
		h5f.create_dataset('p_id_code', data=self.p_id_code)
		h5f.create_dataset('pre_code',  data=self.pre_code)
		h5f.create_dataset('post_code', data=self.post_code)
		h5f.create_dataset('desc_code', data=self.desc_code)
		h5f.create_dataset('a_id',      data=[x.encode("ascii") for x in self.a_id])
		h5f.create_dataset('s_id',      data=self.s_id, dtype='int32')
		h5f.create_dataset('idx',       data=self.idx,  dtype='int32')
		h5f.create_dataset('rule',      data=[x.encode("ascii") for x in self.rule])
		h5f.create_dataset('p_id',      data=[x.encode("ascii") for x in self.p_id])
		h5f.create_dataset('classes',   data=[x.encode("ascii") for x in self.classes])
		h5f.close()
		print(f'Saved data into "{file}"')

if __name__ == '__main__':

	repo_path    = f'data/repo'
	article_path = f'data/article/prune_article_ws'
	mention_path = f'data/mention/prune_article_ws_pid'
	model_path   = f'data/model'
	parts        = list(f'part-{x:05}' for x in range(1))
	# parts        = ['']
	emb_file     = f'data/embedding/prune_article_ws.dim300.emb.bin'
	data_file    = f'{model_path}/data.h5'

	# Load word vectors
	keyed_vectors = KeyedVectors.load_word2vec_format(emb_file, binary=True)

	# Prepare tokenizer
	tokenizer = Tokenizer()
	tokenizer.fit_on_texts([' '.join(keyed_vectors.index2word[1:])])
	num_vocab = len(tokenizer.word_index)+1
	print(f'num_vocab = {num_vocab}')

	# Load StyleMe repository and corpus
	repo   = Repo(repo_path)
	corpus = Corpus(article_path, mention_path, repo, parts=parts)

	# Extract mentions with PID
	mention_list = [mention for mention in corpus.mention_set if mention.p_id.isdigit()]
	num_mention = len(mention_list)
	print(f'num_mention = {num_mention}')

	# Extract mention data
	data = RawData(repo, mention_list)

	# Prepare label encoder
	encoder = LabelEncoder()
	encoder.fit(data.p_id)
	num_label = len(encoder.classes_)
	print(f'num_label = {num_label}')

	# Integer encode the documents and the labels
	data.encode(tokenizer, encoder)

	# Save data
	comment = \
			f'article_path={article_path}\n' \
			f'mention_path={mention_path}\n' \
			f'emb_file={emb_file}\n' \
			f'max_num_sentences={RawData.max_num_sentences}'
	data.save(data_file, comment)

	pass
