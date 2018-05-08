#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import numpy as np

import torch

from .model2 import Model2

class Model2c(Model2):

	def __init__(self, meta):

		from .module import ContextEncoder

		super().__init__(meta)

		# Set dimensions
		lstm_emb_size = 100

		# Create modules
		self.text_encoder = ContextEncoder(meta, self.word_emb, lstm_emb_size)

		# Create label
		self.label_encoder = meta.p_encoder

	def data(self, asmid_list):

		ment_list, repo, corpus, gid = self._data(asmid_list)
		return self.text_encoder.data(ment_list, repo, corpus) + (gid,)

	def data_predict(self, asmid_list):
		ment_list, repo, corpus, gid = self._data(asmid_list)
		return self.text_encoder.data(ment_list, repo, corpus) + (gid,)

	def data_predict_all(self, asmid_list):
		ment_list, repo, corpus, gid = self._data(asmid_list, sp=False)
		return self.text_encoder.data(ment_list, repo, corpus) + (gid,)

	def forward(self, pre_pad, post_pad, title_pad, pid_bag, brand_bag):

		text_emb  = self.text_encoder(pre_pad, post_pad, title_pad, pid_bag, brand_bag)
		text_prob = self.entity_emb(text_emb)

		return text_prob

	def loss(self, text_prob, label):
		return torch.nn.functional.cross_entropy(text_prob, label)

	def predict(self, text_prob):
		return np.argmax(text_prob.cpu().data.numpy(), axis=1)
