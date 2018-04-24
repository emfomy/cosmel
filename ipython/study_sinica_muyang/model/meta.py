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


class Tokenizer(BaseEstimator, TransformerMixin):

	def fit(self, y):
		y = column_or_1d(y, warn=True)
		assert '' not in y
		self.classes_ = np.insert(np.unique(y), 0, '')
		self.index_   = {s: i for i, s in enumerate(self.classes_)}
		return self

	def transform(self, y):
		check_is_fitted(self, 'index_')
		y = column_or_1d(y, warn=True)
		assert '' not in y
		return np.asarray([self.index_[s] for s in y if s in self.index_])

	def fit_transform(self, y):
		self.fit(y)
		self.transform(y)

	def inverse_transform(self, y):
		check_is_fitted(self, 'classes_')
		assert 0 not in y
		return self.classes_[y]

	def transform_sequences(self, yy):
		return [self.transform(y) for y in yy]

	def inverse_transform_sequences(self, yy):
		return [self.inverse_transform(y) for y in yy]


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
			pickle.dump(self, fout, protocol=4)

	@staticmethod
	def load(file):
		print(f'Load data meta from {file}')
		with open(file, 'rb') as fin:
			return pickle.load(fin)
