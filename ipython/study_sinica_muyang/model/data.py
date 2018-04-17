#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import itertools
import json
import os
import pickle
import sys

import numpy as np

import torch

from keras.preprocessing.sequence import pad_sequences

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import label_binarize
from sklearn.preprocessing import LabelBinarizer
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MultiLabelBinarizer

# from sklearn.base import BaseEstimator, TransformerMixin
# from sklearn.utils.validation import column_or_1d

from gensim.models.keyedvectors import KeyedVectors

sys.path.insert(0, os.path.abspath('.'))
from styleme import *


class Asmid:

	def __init__(self, json_str):
		data = json.loads(json_str)
		self.aid     = data['aid']
		self.sid     = data['sid']
		self.mid     = data['mid']
		self.use_gid = data['use_gid']

	def __str__(self):
		return str(self.__dict__)

	def __repr__(self):
		return str(self)

	@property
	def asmid(self):
		return (self.aid, self.sid, self.mid,)


class AsmidList(list):

	def dump(self, file):
		os.makedirs(os.path.dirname(file), exist_ok=True)
		print(f'Dump asmid list into {file}')
		with open(file, 'w') as fout:
			for asmid in self:
				fout.write(asmid+'\n')

	@staticmethod
	def load(file):
		print(f'Load asmid list from {file}')
		with open(file) as fin:
			return AsmidList(Asmid(s) for s in fin)


# class Tokenizer(BaseEstimator, TransformerMixin):

# 	def fit(self, y):
# 		y = column_or_1d(y, warn=True)
# 		assert '' not in y
# 		self.classes_ = np.insert(np.unique(y), 0, '')
# 		return self

# 	def transform(self, y):
# 		y = column_or_1d(y, warn=True)
# 		assert '' not in y
# 		return np.searchsorted(self.classes_, [v for v in y if v in self.classes_])

# 	def fit_transform(self, y):
# 		self.fit(y)
# 		self.transform(y)

# 	def inverse_transform(self, y):
# 		check_is_fitted(self, 'classes_')
# 		assert 0 not in y
# 		return self.classes_[y]

# 	def transform_sequences(self, yy):
# 		return [self.transform(y) for y in yy]

# 	def inverse_transform_sequences(self, yy):
# 		return [self.inverse_transform(y) for y in yy]


class Tokenizer():

	def __init__(self):
		from keras.preprocessing.text import Tokenizer as _Tokenizer
		self._tokenizer = _Tokenizer()

	def fit(self, y):
		self._tokenizer.fit_on_texts(' '.join(y))
		return self

	def transform(self, y):
		return self._tokenizer.texts_to_sequences([' '.join(y)])

	def fit_transform(self, y):
		self.fit(y)
		self.transform(y)

	def transform_sequences(self, yy):
		return self._tokenizer.texts_to_sequences([' '.join(y) for y in yy])

	@property
	def classes_(self):
		return self._tokenizer.word_index


class DatasetMeta:

	def __init__(self, repo, corpus, emb_file):

		# Save pathes
		self.repo_path    = repo.path
		self.article_path = corpus.article_set.path
		self.mention_path = corpus.mention_set.path

		# Load word vectors
		self.keyed_vectors = KeyedVectors.load_word2vec_format(emb_file, binary=True)

		# Prepare tokenizer
		self.tokenizer = Tokenizer()
		self.tokenizer.fit(self.keyed_vectors.index2word[1:])
		num_vocab = len(self.tokenizer.classes_)+1
		print(f'num_vocab   = {num_vocab}')

		# Prepare product encoder
		self.p_encoder = LabelEncoder()
		self.p_encoder.fit(['OSP', 'GP'] + list(repo.id_to_product.keys()))
		num_product = len(self.p_encoder.classes_)
		print(f'num_product = {num_product}')

		# Prepare brand encoder
		self.b_encoder = LabelEncoder()
		self.b_encoder.fit(list(repo.bname_to_brand.keys()))
		num_brand = len(self.b_encoder.classes_)
		print(f'num_brand   = {num_brand}')

	def dump(self, file):
		os.makedirs(os.path.dirname(file), exist_ok=True)
		print(f'Dump data meta into {file}')
		with open(file, 'wb') as fout:
			pickle.dump(self, fout, protocol=4)

	@staticmethod
	def load(file):
		print(f'Load data meta from {file}')
		with open(file, 'rb') as fin:
			return pickle.load(fin)


class BatchData:

	def cuda(self):
		for k, v in vars(self).items():
			setattr(self, k, v.cuda())


class MentionDataset():

	def __init__(self, meta, asmid_list, max_num_sentences=5):

		self.meta = meta

		parts = list(set(m.aid for m in asmid_list))
		self.repo   = Repo(meta.repo_path)
		self.corpus = Corpus(meta.article_path, meta.mention_path, parts=parts)

		self.mention_list = [self.corpus.id_to_mention[asmid.asmid] for asmid in asmid_list]
		for m in self.mention_list:
			if m.gid == 'NAP': m.set_gid('GP')
			if m.pid == 'NAP': m.set_pid('GP')
		for m, asmid in zip(self.mention_list, asmid_list):
			if not asmid.use_gid: m.set_gid(m.pid)

		self.max_num_sentences = max_num_sentences

		# Get length
		self.title_maxlen = 80
		self.loacl_maxlen = self.title_maxlen*(max_num_sentences+1)

		# Load tokenizer and encoder
		self.tokenizer = meta.tokenizer
		self.p_encoder = meta.p_encoder
		self.b_encoder = meta.b_encoder

		# Prepare product binarizer
		self.p_binarizer = LabelBinarizer()
		self.p_binarizer.fit(meta.p_encoder.classes_)
		np.testing.assert_array_equal(meta.p_encoder.classes_, self.p_binarizer.classes_)

		# Prepare product multi-binarizer
		self.p_multibinarizer = MultiLabelBinarizer(classes=meta.p_encoder.classes_)
		self.p_multibinarizer.fit([])
		np.testing.assert_array_equal(meta.p_encoder.classes_, self.p_multibinarizer.classes_)

		# Prepare brand multi-binarizer
		self.b_multibinarizer = MultiLabelBinarizer(classes=meta.b_encoder.classes_)
		self.b_multibinarizer.fit([])
		np.testing.assert_array_equal(meta.b_encoder.classes_, self.b_multibinarizer.classes_)

	def __len__(self):
		return len(self.mention_list)

	def __getitem__(self, idx):

		if isinstance(idx, int):
			sublist = [self.mention_list[idx]]
		else:
			sublist = np.asarray(self.mention_list)[idx]

		# Load Data
		gid = [mention.gid for mention in sublist]

		# Load context
		raw_title = [ \
				mention.article[0].txts for mention in sublist \
		]
		raw_pre  = [ \
				list(itertools.chain( \
						itertools.chain.from_iterable( \
								s.txts for s in mention.article[relu(mention.sid-self.max_num_sentences):mention.sid] \
						), \
						mention.sentence_pre_().txts \
				)) for mention in sublist \
		]
		raw_post = [ \
				list(itertools.chain( \
						mention.sentence_post_().txts, \
						itertools.chain.from_iterable( \
								s.txts for s in mention.article[mention.sid+1:mention.sid+1+self.max_num_sentences] \
						) \
				)) for mention in sublist \
		]

		# Load bag
		raw_pid_bag   = [set(m.pid for m in mention.bundle if m.rule == 'P_rule1') for mention in sublist]
		raw_brand_bag = [ \
				set(self.repo.bname_to_brand[t[0]][0] \
						for t in itertools.chain.from_iterable(sentence.zip3 for sentence in mention.article) if t[2] == 'Brand' \
				) for mention in sublist \
		]

		# Encode
		gid_code   = self.p_encoder.transform(gid)
		title_code = self.tokenizer.transform_sequences(raw_title)
		pre_code   = self.tokenizer.transform_sequences(raw_pre)
		post_code  = self.tokenizer.transform_sequences(raw_post)
		pid_bag    = self.p_multibinarizer.transform(raw_pid_bag)
		brand_bag  = self.b_multibinarizer.transform(raw_brand_bag)
		text_1hot  = self.p_binarizer.transform(gid)

		# Pad
		title_pad  = pad_sequences(title_code, padding='pre')
		pre_pad    = pad_sequences(pre_code,   padding='pre')
		post_pad   = pad_sequences(post_code,  padding='post')

		# Convert to PyTorch
		retval = BatchData()
		retval.gid_code  = torch.from_numpy(gid_code).long()
		retval.title_pad = torch.from_numpy(title_pad).long()
		retval.pre_pad   = torch.from_numpy(pre_pad).long()
		retval.post_pad  = torch.from_numpy(post_pad).long()
		retval.pid_bag   = torch.from_numpy(pid_bag).float()
		retval.brand_bag = torch.from_numpy(brand_bag).float()
		retval.text_1hot = torch.from_numpy(text_1hot).float()

		return vars(retval)


class ProductDataset():

	def __init__(self, meta):

		self.meta = meta
		self.repo = Repo(meta.repo_path)

		self.product_list = list(self.repo.product_set)

		# Load tokenizer and encoder
		self.tokenizer = meta.tokenizer
		self.p_encoder = meta.p_encoder

		# Get length
		self.desc_maxlen = max([len(product.descr_ws.txts) for product in self.product_list])
		self.name_maxlen = max([len(list(product.brand) + product.name_ws.txts) for product in self.product_list])

		# Prepare product binarizer
		self.p_binarizer = LabelBinarizer()
		self.p_binarizer.fit(meta.p_encoder.classes_)
		np.testing.assert_array_equal(meta.p_encoder.classes_, self.p_binarizer.classes_)

	def __len__(self):
		return len(self.product_list)

	def __getitem__(self, idx):

		if isinstance(idx, int):
			sublist = [self.product_list[idx]]
		else:
			sublist = np.asarray(self.product_list)[idx]

		# Load Data
		pid           = [product.pid for product in sublist]

		# Load context
		raw_name      = [list(product.brand) + product.name_ws.txts for product in sublist]
		# raw_name_pre  = [list(product.brand) + product.infix_ws_().txts for product in sublist]
		# raw_name_post = [product.suffix_ws_().txts for product in sublist]
		raw_desc      = [product.descr_ws.txts for product in sublist]

		# Encode
		pid_code       = self.p_encoder.transform(pid)
		desc_code      = self.tokenizer.transform_sequences(raw_desc)
		name_code      = self.tokenizer.transform_sequences(raw_name)
		# name_pre_code  = self.tokenizer.transform_sequences(raw_name_pre)
		# name_post_code = self.tokenizer.transform_sequences(raw_name_post)
		desc_1hot      = self.p_binarizer.transform(pid)

		# Pad
		desc_pad = pad_sequences(desc_code, padding='pre')
		name_pad = pad_sequences(name_code, padding='pre')

		# Convert to PyTorch
		retval = BatchData()
		retval.product_code    = torch.from_numpy(pid_code).long()
		retval.desc_pad        = torch.from_numpy(desc_pad).long()
		retval.name_pad        = torch.from_numpy(name_pad).long()
		retval.desc_1hot       = torch.from_numpy(desc_1hot).float()

		return vars(retval)
