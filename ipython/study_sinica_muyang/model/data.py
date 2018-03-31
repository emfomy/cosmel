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
from sklearn.preprocessing import MultiLabelBinarizer
import sklearn.model_selection

from gensim.models.keyedvectors import KeyedVectors

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

class Data:

	_attr = ['gid_code', 'title_code', 'pre_code', 'post_code', 'desc_code', 'pid_bag', 'brand_bag', \
			'aid', 'sid', 'mid', 'rule', 'gid']

	def __getitem__(self, key):
		data = Data()
		for attr in Data._attr:
			setattr(data, attr, getattr(self, attr)[key])
		return data

	@property
	def size(self):
		return len(self.gid_code)

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
		self.aid  = [mention.aid  for mention in mention_list]
		self.sid  = [mention.sid  for mention in mention_list]
		self.mid  = [mention.mid  for mention in mention_list]
		self.rule = [mention.rule for mention in mention_list]
		self.gid  = [mention.gid  for mention in mention_list]

		self.title = [ \
				' '.join(mention.article[0].txts) for mention in mention_list \
		]
		self.pre  = [ \
				' '.join(itertools.chain( \
						itertools.chain.from_iterable( \
								s.txts for s in mention.article[max(mention.sid-RawData.max_num_sentences, 0):mention.sid] \
						), \
						mention.sentence_pre.txts, mention.mention.txts \
				)) for mention in mention_list \
		]
		self.post = [ \
				' '.join(itertools.chain( \
						mention.mention.txts, mention.sentence_post.txts, \
						itertools.chain.from_iterable( \
								s.txts for s in mention.article[mention.sid+1:mention.sid+1+RawData.max_num_sentences] \
						) \
				)) for mention in mention_list \
		]
		self.desc  = [' '.join(repo.id_to_product[mention.gid].descr_ws.txts) for mention in mention_list]

		self.pid_doc   = [set(m.pid for m in mention.bundle if m.rule == 'P_rule1') for mention in mention_list]
		self.brand_doc = [ \
				set(repo.bname_to_brand[t[0]][0] \
						for t in itertools.chain.from_iterable(sentence.zip3 for sentence in mention.article) if t[2] == 'Brand' \
				) for mention in mention_list \
		]

	def encode(self, tokenizer, p_encoder, b_encoder, p_multibinarizer, b_multibinarizer):
		self.gid_code   = p_encoder.transform(self.gid)
		self.title_code = pad_sequences(tokenizer.texts_to_sequences(self.title), padding='post')
		self.pre_code   = pad_sequences(tokenizer.texts_to_sequences(self.pre),   padding='pre')
		self.post_code  = pad_sequences(tokenizer.texts_to_sequences(self.post),  padding='post')
		self.desc_code  = pad_sequences(tokenizer.texts_to_sequences(self.desc),  padding='post')

		self.pid_bag    = p_multibinarizer.transform(self.pid_doc)
		self.brand_bag  = b_multibinarizer.transform(self.brand_doc)

		self.p_classes  = p_encoder.classes_
		self.b_classes  = b_encoder.classes_

	def save(self, file, comment=''):
		os.makedirs(os.path.dirname(file), exist_ok=True)
		h5f = h5py.File(file, 'w')
		h5f.create_dataset('comment',    data=comment)
		h5f.create_dataset('gid_code',   data=self.gid_code)
		h5f.create_dataset('title_code', data=self.title_code)
		h5f.create_dataset('pre_code',   data=self.pre_code)
		h5f.create_dataset('post_code',  data=self.post_code)
		h5f.create_dataset('desc_code',  data=self.desc_code)
		h5f.create_dataset('pid_bag',    data=self.pid_bag)
		h5f.create_dataset('brand_bag',  data=self.brand_bag)
		h5f.create_dataset('aid',        data=[x.encode("ascii") for x in self.aid])
		h5f.create_dataset('sid',        data=self.sid, dtype='int32')
		h5f.create_dataset('mid',        data=self.mid, dtype='int32')
		h5f.create_dataset('rule',       data=[x.encode("ascii") for x in self.rule])
		h5f.create_dataset('gid',        data=[x.encode("ascii") for x in self.gid])
		# h5f.create_dataset('p_classes',  data=[x.encode("ascii") for x in self.p_classes])
		# h5f.create_dataset('b_classes',  data=[x.encode("ascii") for x in self.b_classes])
		h5f.close()
		print(f'Saved data into "{file}"')

if __name__ == '__main__':

	assert len(sys.argv) > 3
	ver = sys.argv[1]

	use_pid      = (sys.argv[3] != '0')
	use_pid_str  = '_use_pid' if use_pid else '_use_gid'

	target_ver   = f''
	target_ver   = f'_{sys.argv[2]}'
	data_root    = f'data/{ver}'
	repo_root    = f'{data_root}/repo'
	article_root = f'{data_root}/article/pruned_article_role'
	mention_root = f'{data_root}/mention/pruned_article{target_ver}'
	model_root   = f'{data_root}/model'
	parts        = ['']
	parts        = list(f'part-{x:05}' for x in range(1))
	emb_file     = f'{data_root}/embedding/pruned_article.dim300.emb.bin'
	data_file    = f'{model_root}/data{target_ver}{use_pid_str}.h5'

	# Load word vectors
	keyed_vectors = KeyedVectors.load_word2vec_format(emb_file, binary=True)

	# Prepare tokenizer
	tokenizer = Tokenizer()
	tokenizer.fit_on_texts([' '.join(keyed_vectors.index2word[1:])])
	num_vocab = len(tokenizer.word_index)+1
	print(f'num_vocab = {num_vocab}')

	# Load StyleMe repository and corpus
	repo   = Repo(repo_root)
	corpus = Corpus(article_root, mention_root, parts=parts)

	if use_pid:
		for mention in corpus.mention_set:
			if mention.pid:
				mention.set_gid(mention.pid)
			else:
				mention.set_gid('')
				mention.set_rule('')

	# Extract mentions with PID
	mention_list = [mention for mention in corpus.mention_set if mention.gid.isdigit()]
	num_mention = len(mention_list)
	print(f'num_mention = {num_mention}')

	# Extract mention data
	data = RawData(repo, mention_list)

	# Prepare product encoder
	p_encoder = LabelEncoder()
	p_encoder.fit(list(repo.id_to_product))
	num_label = len(p_encoder.classes_)
	print(f'num_label   = {num_label}')

	# Prepare brand encoder
	b_encoder = LabelEncoder()
	b_encoder.fit([b for s in data.brand_doc for b in s])
	num_brand = len(b_encoder.classes_)
	print(f'num_brand   = {num_brand}')

	# Prepare product multi-binarizer
	p_multibinarizer = MultiLabelBinarizer(classes=p_encoder.classes_.tolist())
	p_multibinarizer.fit(data.pid_doc)

	# Prepare brand multi-binarizer
	b_multibinarizer = MultiLabelBinarizer(classes=b_encoder.classes_.tolist())
	b_multibinarizer.fit(data.brand_doc)

	# Integer encode the docments and the labels
	data.encode(tokenizer, p_encoder, b_encoder, p_multibinarizer, b_multibinarizer)

	# Save data
	comment = \
			f'article_root={article_root}\n' \
			f'mention_root={mention_root}\n' \
			f'emb_file={emb_file}\n' \
			f'max_num_sentences={RawData.max_num_sentences}'
	data.save(data_file, comment)

	pass
