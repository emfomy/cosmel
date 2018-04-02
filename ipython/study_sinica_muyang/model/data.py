#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import copy
import itertools
import os
import pickle
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

class DataPack:

	class Raw():

		def __str__(self):
			return str(list(self.__dict__.keys()))

		def __repr__(self):
			return str(self)


	class Data():

		def __str__(self):
			return str(list(self.__dict__.keys()))

		def __repr__(self):
			return str(self)

		def train_test_split(self, *args, **kwargs):
			train_data = DataPack.Data()
			test_data  = DataPack.Data()
			keys = list(self.__dict__.keys())
			splitting = sklearn.model_selection.train_test_split(*(getattr(self, key) for key in keys), *args, **kwargs)
			for i, key in enumerate(keys):
				setattr(train_data, key, splitting[2*i])
				setattr(test_data,  key, splitting[2*i+1])
			return train_data, test_data


	class Info():

		def __str__(self):
			return str(list(self.__dict__.keys()))

		def __repr__(self):
			return str(self)


	def __init__(self):
		self.data = self.Data()
		self.info = self.Info()

	def __str__(self):
		return str(self.__dict__)

	def __repr__(self):
		return str(self)

	def extract(self, repo, corpus, use_gid=True, max_num_sentences=5):

		# Declare raw data
		self.data.raw = self.Raw()
		self.info.raw = self.Raw()

		# Extract mention
		if use_gid:
			mention_list = [mention for mention in corpus.mention_set if mention.gid.isdigit()]
		else:
			mention_list = [mention for mention in corpus.mention_set if mention.pid.isdigit()]

		# Load Info
		self.info.article_root      = corpus.article_set.path
		self.info.mention_root      = corpus.mention_bundle_set.path
		self.info.max_num_sentences = max_num_sentences

		# Load Data
		self.data.aid  = np.asarray([mention.aid  for mention in mention_list])
		self.data.sid  = np.asarray([mention.sid  for mention in mention_list])
		self.data.mid  = np.asarray([mention.mid  for mention in mention_list])
		self.data.rule = np.asarray([mention.rule for mention in mention_list])

		if use_gid:
			self.data.gid  = np.asarray([mention.gid for mention in mention_list])
		else:
			self.data.gid  = np.asarray([mention.pid for mention in mention_list])

		self.data.raw.title = [ \
				' '.join(mention.article[0].txts) for mention in mention_list \
		]
		self.data.raw.pre  = [ \
				' '.join(itertools.chain( \
						itertools.chain.from_iterable( \
								s.txts for s in mention.article[relu(mention.sid-max_num_sentences):mention.sid] \
						), \
						mention.sentence_pre.txts, mention.mention.txts \
				)) for mention in mention_list \
		]
		self.data.raw.post = [ \
				' '.join(itertools.chain( \
						mention.mention.txts, mention.sentence_post.txts, \
						itertools.chain.from_iterable( \
								s.txts for s in mention.article[mention.sid+1:mention.sid+1+max_num_sentences] \
						) \
				)) for mention in mention_list \
		]

		self.data.raw.desc  = [' '.join(repo.id_to_product[gid].descr_ws.txts) for gid in self.data.gid]

		self.data.raw.pid_doc   = [set(m.pid for m in mention.bundle if m.rule == 'P_rule1') for mention in mention_list]
		self.data.raw.brand_doc = [ \
				set(repo.bname_to_brand[t[0]][0] \
						for t in itertools.chain.from_iterable(sentence.zip3 for sentence in mention.article) if t[2] == 'Brand' \
				) for mention in mention_list \
		]

	def encode(self, repo, tokenizer, p_encoder, b_encoder, p_multibinarizer, b_multibinarizer):

		# Store classes
		self.info.tokenizer        = tokenizer
		self.info.p_encoder        = p_encoder
		self.info.b_encoder        = b_encoder
		self.info.p_multibinarizer = p_multibinarizer
		self.info.b_multibinarizer = b_multibinarizer

		# Encode products
		self.info.raw.product       = [' '.join(list(repo.id_to_product[pid].brand) + repo.id_to_product[pid].name_ws.txts) \
				for pid in p_encoder.classes_]
		self.info.product_code = pad_sequences(tokenizer.texts_to_sequences(self.info.raw.product), padding='post')
		self.info.product_len  = np.asarray([len(p.split(' ')) for p in self.info.raw.product])

		# Encode corpus
		self.data.gid_code   = p_encoder.transform(self.data.gid)
		self.data.title_code = pad_sequences(tokenizer.texts_to_sequences(self.data.raw.title), padding='post')
		self.data.pre_code   = pad_sequences(tokenizer.texts_to_sequences(self.data.raw.pre),   padding='pre')
		self.data.post_code  = pad_sequences(tokenizer.texts_to_sequences(self.data.raw.post),  padding='post')
		self.data.desc_code  = pad_sequences(tokenizer.texts_to_sequences(self.data.raw.desc),  padding='post')

		self.data.pid_bag    = p_multibinarizer.transform(self.data.raw.pid_doc)
		self.data.brand_bag  = b_multibinarizer.transform(self.data.raw.brand_doc)

	def prune(self):
		del self.data.raw
		del self.info.raw

	def dump(self, file):
		print(f'Dump data into {file}')
		with open(file, 'wb') as fout:
			pickle.dump(self, fout, protocol=4)

	@staticmethod
	def load(file):
		print(f'Load data from {file}')
		with open(file, 'rb') as fin:
			return pickle.load(fin)

	def train_test_split(self, *args, **kwargs):
		assert not hasattr(self.data, 'raw')
		assert not hasattr(self.data, 'raw')

		train_pack      = DataPack()
		test_pack       = DataPack()

		train_pack.info = copy.deepcopy(self.info)
		test_pack.info  = copy.deepcopy(self.info)

		train_pack.data, test_pack.data = self.data.train_test_split(*args, **kwargs)

		return train_pack, test_pack

if __name__ == '__main__':

	if len(sys.argv) <= 1:
		print(f'Usage: {sys.argv[0]} <ver> [mention_suffix]\n')

	assert len(sys.argv) > 1
	ver = sys.argv[1]

	target_ver    = f''
	if len(sys.argv) > 2: target_ver = f'_{sys.argv[2]}'
	data_root     = f'data/{ver}'
	repo_root     = f'{data_root}/repo'
	article_root  = f'{data_root}/article/pruned_article_role'
	mention_root  = f'{data_root}/mention/pruned_article{target_ver}'
	model_root    = f'{data_root}/model'
	parts         = ['']
	# parts         = list(f'part-{x:05}' for x in range(1))
	emb_file      = f'{data_root}/embedding/pruned_article.dim300.emb.bin'

	pack_pid_file       = f'{model_root}/pruned_article{target_ver}.data.pid.pkl'
	pack_gid_file       = f'{model_root}/pruned_article{target_ver}.data.gid.pkl'
	pack_pid_train_file = f'{model_root}/pruned_article{target_ver}.data.pid.train.pkl'
	pack_pid_test_file  = f'{model_root}/pruned_article{target_ver}.data.pid.test.pkl'
	pack_gid_train_file = f'{model_root}/pruned_article{target_ver}.data.gid.train.pkl'
	pack_gid_test_file  = f'{model_root}/pruned_article{target_ver}.data.gid.test.pkl'

	# Load StyleMe repository and corpus
	repo   = Repo(repo_root)
	corpus = Corpus(article_root, mention_root, parts=parts)

	# Extract mention data
	pack_pid = DataPack()
	pack_gid = DataPack()

	pack_pid.extract(repo, corpus, False)
	pack_gid.extract(repo, corpus, True)

	num_mention_pid = len(pack_pid.data.gid)
	num_mention_gid = len(pack_gid.data.gid)
	print(f'num_mention (PID) = {num_mention_pid}')
	print(f'num_mention (GID) = {num_mention_gid}')

	# Load word vectors
	keyed_vectors = KeyedVectors.load_word2vec_format(emb_file, binary=True)

	# Prepare tokenizer
	tokenizer = Tokenizer()
	tokenizer.fit_on_texts([' '.join(keyed_vectors.index2word[1:])])
	num_vocab = len(tokenizer.word_index)+1
	print(f'num_vocab   = {num_vocab}')

	# Prepare product encoder
	p_encoder = LabelEncoder()
	p_encoder.fit(list(repo.id_to_product.keys()))
	num_product = len(p_encoder.classes_)
	print(f'num_product = {num_product}')

	# Prepare brand encoder
	b_encoder = LabelEncoder()
	b_encoder.fit([brand[0] for brand in repo.brand_set])
	num_brand = len(b_encoder.classes_)
	print(f'num_brand   = {num_brand}')

	# Prepare product multi-binarizer
	p_multibinarizer = MultiLabelBinarizer(classes=p_encoder.classes_.tolist())
	p_multibinarizer.fit(pack_pid.data.raw.pid_doc + pack_gid.data.raw.pid_doc)

	# Prepare brand multi-binarizer
	b_multibinarizer = MultiLabelBinarizer(classes=b_encoder.classes_.tolist())
	b_multibinarizer.fit(pack_pid.data.raw.brand_doc + pack_gid.data.raw.brand_doc)

	# Integer encode the docments and the labels
	pack_pid.encode(repo, tokenizer, p_encoder, b_encoder, p_multibinarizer, b_multibinarizer)
	pack_gid.encode(repo, tokenizer, p_encoder, b_encoder, p_multibinarizer, b_multibinarizer)

	# Delete raw data
	pack_pid.prune()
	pack_gid.prune()

	# Split train and test
	pack_pid_train, pack_pid_test = pack_pid.train_test_split(test_size=0.3, random_state=0, shuffle=True)
	pack_gid_train, pack_gid_test = pack_gid.train_test_split(test_size=0.3, random_state=0, shuffle=True)

	num_train_pid = len(pack_pid_train.data.gid)
	num_test_pid  = len(pack_pid_test.data.gid)
	num_train_gid = len(pack_gid_train.data.gid)
	num_test_gid  = len(pack_gid_test.data.gid)
	print(f'num_train (PID) = {num_train_pid}')
	print(f'num_test  (PID) = {num_test_pid}')
	print(f'num_train (GID) = {num_train_gid}')
	print(f'num_test  (GID) = {num_test_gid}')

	# Save as pickle
	pack_pid.dump(f'{model_root}/pruned_article{target_ver}.data.pid.pkl')
	pack_gid.dump(f'{model_root}/pruned_article{target_ver}.data.gid.pkl')

	pack_pid_train.dump(f'{model_root}/pruned_article{target_ver}.data.pid.train.pkl')
	pack_pid_test.dump(f'{model_root}/pruned_article{target_ver}.data.pid.test.pkl')

	pack_gid_train.dump(f'{model_root}/pruned_article{target_ver}.data.gid.train.pkl')
	pack_gid_test.dump(f'{model_root}/pruned_article{target_ver}.data.gid.test.pkl')

	pass
