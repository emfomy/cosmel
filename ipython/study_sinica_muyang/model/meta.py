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

from sklearn.preprocessing import LabelBinarizer
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MultiLabelBinarizer

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted
from sklearn.utils.validation import column_or_1d

from gensim.models.keyedvectors import KeyedVectors

sys.path.insert(0, os.path.abspath('.'))
from styleme import *


class Asmid:

	def __init__(self, json_str):
		data = json.loads(json_str)
		self.aid = data['aid']
		self.sid = data['sid']
		self.mid = data['mid']
		self.pid = data['pid']
		self.gid = data['gid']

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
				fout.write(asmid+'\n')

	@staticmethod
	def load(file):
		print(f'Load asmid list from {file}')
		with open(file) as fin:
			return AsmidList(Asmid(s) for s in fin)

	def gid_to_mtype(self):
		for asmid in self.__data:
			if asmid.gid.isdigit(): asmid.gid = 'PID'

	def pid_to_mtype(self):
		for asmid in self.__data:
			if asmid.pid.isdigit(): asmid.pid = 'PID'

	def filter_sp(self):
		self.__data = [asmid for asmid in self.__data if asmid.gid.isdigit()]


class Tokenizer(BaseEstimator, TransformerMixin):

	def __init__(self, classes=None):

		super().__init__()

		if classes: self.classes_ = classes
		self.__fit_index()

	def fit(self, y):
		y = column_or_1d(y, warn=True)
		self.classes_ = np.unique(y)
		self.__fit_index()
		return self

	def __fit_index(self):
		self.index_ = {s: i+1 for i, s in enumerate(self.classes_)}

	def transform(self, y):
		check_is_fitted(self, 'index_')
		y = column_or_1d(y, warn=True)
		return [self.index_[s] for s in y if s in self.index_]

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


class DataSetMeta:

	class Core:

		def __init__(self, repo, corpus, emb_file):

			# Save pathes
			self.repo_path    = repo.path
			self.article_path = corpus.article_set.path
			self.mention_path = corpus.mention_set.path

			# Save word vectors
			self.keyed_vectors = KeyedVectors.load_word2vec_format(emb_file, binary=True)

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
		self.tokenizer = Tokenizer(self.keyed_vectors.index2word[1:])
		num_vocab = len(self.tokenizer.classes_)+1
		print(f'num_vocab   = {num_vocab}')

		# Prepare padder
		self.padder = Padder()

		# Prepare product encoder
		self.p_encoder = LabelEncoder()
		self.p_encoder.fit(['GP' + 'OSP'] + self.pids)
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
