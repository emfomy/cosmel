#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import collections.abc
import itertools
import json
import os
import pickle
import sys

import numpy as np

import torch

from sklearn.preprocessing import LabelEncoder as _LabelEncoder
from sklearn.preprocessing import LabelBinarizer
from sklearn.preprocessing import MultiLabelBinarizer

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted
from sklearn.utils.validation import column_or_1d

sys.path.insert(0, os.path.abspath('.'))
from styleme import *


################################################################################################################################
# ASMID
#

class Asmid:

	def __init__(self, aid, sid, mid, pid, gid):
		self.aid = aid
		self.sid = sid
		self.mid = mid
		self.pid = pid
		self.gid = gid

	def __str__(self):
		return str(self.__dict__)

	def __repr__(self):
		return str(self)

	@property
	def asmid(self):
		return (self.aid, self.sid, self.mid,)


class AsmidList(collections.abc.Sequence):

	def __init__(self, data):
		super().__init__()
		self.__data = list(data)

	def __contains__(self, item):
		return item in self.__data

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def __str__(self):
		return str(self.__data)

	def __repr__(self):
		return str(self)

	def dump(self, file):
		os.makedirs(os.path.dirname(file), exist_ok=True)
		print(f'Dump asmid list into {file}')
		with open(file, 'w') as fout:
			for asmid in self.__data:
				fout.write(json.dumps(vars(asmid))+'\n')

	@staticmethod
	def load(file):
		print(f'Load asmid list from {file}')
		with open(file) as fin:
			return AsmidList(Asmid(**json.loads(s)) for s in fin)

	def train_test_split(self, **kwargs):
		from sklearn.model_selection import train_test_split
		train_list, test_list = train_test_split(self.__data, **kwargs)
		return AsmidList(train_list), AsmidList(test_list)

	def gid_to_mtype(self):
		for asmid in self.__data:
			if asmid.gid.isdigit(): asmid.gid = 'PID'

	def pid_to_mtype(self):
		for asmid in self.__data:
			if asmid.pid.isdigit(): asmid.pid = 'PID'

	def filter_sp(self):
		self.__data = [asmid for asmid in self.__data if asmid.gid.isdigit()]


################################################################################################################################
# Encoder
#

class LabelEncoder(_LabelEncoder):

	def transform(self, y, unknown=False):
		if not unknown:
			return super().transform(y)
		else:
			y = column_or_1d(y, warn=True)
			idx = np.in1d(y, self.classes_)
			retval = -np.ones(y.shape, dtype='int64')
			retval[idx] = super().transform(y[idx])
			return retval

	def inverse_transform(self, y):
		y = column_or_1d(y, warn=True)
		idx = (y != -1)
		retval = np.empty(y.shape, dtype=self.classes_.dtype)
		retval[idx] = super().inverse_transform(y[idx])
		return retval

################################################################################################################################
# Tokenizer & Padder
#

class Tokenizer(BaseEstimator, TransformerMixin):

	def __init__(self, index=None):

		super().__init__()

		if index:
			self.index_ = index

			from collections import defaultdict
			classes = defaultdict(list)
			for w, i in self.index_.items():
				classes[i].append(w)
			self.classes_ = dict(classes)

	def fit(self, y):
		y = column_or_1d(y, warn=True)
		self.classes_ = np.unique(y)
		self.index_ = {w: i+1 for i, w in enumerate(self.classes_)}
		return self

	def transform(self, y):
		check_is_fitted(self, 'index_')
		y = column_or_1d(y, warn=True)
		return [self.index_[w] for w in y if w in self.index_]

	def fit_transform(self, y):
		self.fit(y)
		self.transform(y)

	def inverse_transform(self, y):
		check_is_fitted(self, 'classes_')
		assert 0 not in y
		return self.classes_[y-1]

	def transform_sequences(self, yy):
		return [self.transform(y) for y in yy]

	def inverse_transform_sequences(self, yy):
		return [self.inverse_transform(y) for y in yy]


class Padder():

	def pad(self, yy, dtype='int64', padding='pre', value=0.):
		numy   = len(yy)
		maxlen = max(map(len, yy))
		retval = (np.ones((numy, maxlen)) * value).astype(dtype)
		for idx, y in enumerate(yy):
			if not len(y):
				continue

			assert value not in y

			if padding == 'post':
				retval[idx, :len(y)] = y
			elif padding == 'pre':
				retval[idx, -len(y):] = y
			else:
				raise ValueError(f'Padding type "{padding}" not understood')
		return retval

	def __call__(self, *args, **kwargs):
		return self.pad(*args, **kwargs)


################################################################################################################################
# Data Set Meta
#

class DataSetMeta:

	class Core:

		def __init__(self, repo, corpus, emb_file):

			# Save pathes
			self.repo_path    = repo.path
			self.article_path = corpus.article_set.path
			self.mention_path = corpus.mention_set.path

			# Save word vectors
			from gensim.models.keyedvectors import KeyedVectors
			keyed_vectors = KeyedVectors.load_word2vec_format(emb_file, binary=True)
			b_set = set(repo.bname_to_brand.keys())
			w_set = set(keyed_vectors.index2word[1:])
			o_set = w_set - b_set
			assert b_set <= w_set

			self.word_index = {w: i+1 for i, b in enumerate(repo.brand_set) for w in b}
			n = len(repo.brand_set)+1
			self.word_index.update({w: i+n for i, w in enumerate(o_set)})
			n+=len(o_set)

			self.word_vector = np.zeros((n, keyed_vectors.vector_size), dtype='float32')
			for b in repo.brand_set:
				self.word_vector[self.word_index[b[0]]] = np.mean(keyed_vectors[b], axis=0)
			for w in o_set:
				self.word_vector[self.word_index[w]] = keyed_vectors[w]

			# Save product ID and brand names
			self.pids   = list(repo.id_to_product.keys())
			self.bnames = list(b[0] for b in repo.brand_set)

	@staticmethod
	def new(repo, corpus, emb_file):
		return DataSetMeta(DataSetMeta.Core(repo, corpus, emb_file))

	def __init__(self, core):

		# Initlaize core
		self.core = core
		for k, v in vars(self.core).items():
			setattr(self, k, v)

		# Prepare tokenizer
		self.tokenizer = Tokenizer(self.word_index)
		num_vocab = len(self.tokenizer.classes_)+1
		print(f'num_vocab   = {num_vocab}')
		assert num_vocab == self.word_vector.shape[0]

		# Prepare padder
		self.padder = Padder()

		# Prepare product encoder
		self.p_encoder = LabelEncoder()
		self.p_encoder.fit(self.pids)
		num_product = len(self.p_encoder.classes_)
		print(f'num_product = {num_product}')

		# Prepare brand encoder
		self.b_encoder = LabelEncoder()
		self.b_encoder.fit(self.bnames)
		num_brand = len(self.b_encoder.classes_)
		print(f'num_brand   = {num_brand}')

		# Prepare product binarizer
		self.p_binarizer = LabelBinarizer()
		self.p_binarizer.fit(self.p_encoder.classes_)
		np.testing.assert_array_equal(self.p_encoder.classes_, self.p_binarizer.classes_)

		# Prepare brand binarizer
		self.b_binarizer = LabelBinarizer()
		self.b_binarizer.fit(self.b_encoder.classes_)
		np.testing.assert_array_equal(self.b_encoder.classes_, self.b_binarizer.classes_)

		# Prepare product multi-binarizer
		self.p_multibinarizer = MultiLabelBinarizer(classes=self.p_encoder.classes_)
		self.p_multibinarizer.fit([])
		np.testing.assert_array_equal(self.p_encoder.classes_, self.p_multibinarizer.classes_)

		# Prepare brand multi-binarizer
		self.b_multibinarizer = MultiLabelBinarizer(classes=self.b_encoder.classes_)
		self.b_multibinarizer.fit([])
		np.testing.assert_array_equal(self.b_encoder.classes_, self.b_multibinarizer.classes_)

	def dump(self, file):
		os.makedirs(os.path.dirname(file), exist_ok=True)
		print(f'Dump data meta into {file}')
		with open(file, 'wb') as fout:
			pickle.dump(self.core, fout, protocol=4)

	@staticmethod
	def load(file):
		print(f'Load data meta from {file}')
		with open(file, 'rb') as fin:
			return DataSetMeta(pickle.load(fin))
