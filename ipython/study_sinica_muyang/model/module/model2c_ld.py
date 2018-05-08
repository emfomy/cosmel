#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import numpy as np

import torch

from .model2 import Model2

class Model2c_ld(Model2):

	def __init__(self, meta):

		from .module import LocalContextEncoder, DocumentEncoder

		super().__init__(meta)

		# Set dimensions
		w2v_emb_size = self.word_emb.embedding_dim

		# Set size
		self.output_size = w2v_emb_size
		lstm_emb_size = 100

		# Create modules
		self.local_encoder = LocalContextEncoder(meta, self.word_emb, lstm_emb_size)
		self.docu_encoder  = DocumentEncoder(meta, self.word_emb)

		concat_size = self.local_encoder.output_size + self.docu_encoder.output_size
		self.linear = torch.nn.Linear(concat_size, self.output_size)

		# Create label
		self.label_encoder = meta.p_encoder

	def data(self, asmid_list):

		ment_list, repo, corpus, gid = self._data(asmid_list)

		pre_pad, post_pad  = self.local_encoder.data(ment_list, repo, corpus)
		pid_bag, brand_bag = self.docu_encoder.data(ment_list, repo, corpus)

		return pre_pad, post_pad, pid_bag, brand_bag, gid

	def forward(self, pre_pad, post_pad, pid_bag, brand_bag):

		local_emb = self.local_encoder(pre_pad, post_pad)
		docu_emb  = self.docu_encoder(pid_bag, brand_bag)
		text_emb  = self.linear(torch.cat((local_emb, docu_emb), dim=1)).clamp(min=0)
		text_prob = self.entity_emb(text_emb)

		return text_prob

	def loss(self, text_prob, label):
		return torch.nn.functional.cross_entropy(text_prob, label)

	def predict(self, text_prob):
		return np.argmax(text_prob.cpu().data.numpy(), axis=1)
