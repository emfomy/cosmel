#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os

import torch

class Model(torch.nn.Module):

	from .data import MentionData
	from .data import ProductData

	def __init__(self, meta):

		super().__init__()

		self.meta = meta

		# Get sizes
		num_vocab = meta.word_vector.shape[0]

		# Prepare embeddings
		vocab_embedding = meta.word_vector.copy()

		# Set dimensions
		self.w2v_emb_size = meta.word_vector.shape[1]

		# Create modules
		self.word_emb = torch.nn.Embedding(num_vocab, self.w2v_emb_size)
		self.word_emb.weight.data = torch.from_numpy(vocab_embedding)
		# self.word_emb.weight.requires_grad = False

	def forward(self, *args, **kwargs):
		raise NotImplementedError

	def loss(self, *args, **kwargs):
		raise NotImplementedError

	def predict(self, *args, **kwargs):
		raise NotImplementedError

	def ment_data(self, ment_list):
		return self.MentionData(self, ment_list, _all=False)

	def prod_data(self):
		return self.ProductData(self)

	def ment_data_all(self, ment_list):
		return self.MentionData(self, ment_list, _all=True)

	def save(self, file):
		os.makedirs(os.path.dirname(file), exist_ok=True)
		torch.save(self.state_dict(), file)

	def load(self, file):
		self.load_state_dict(torch.load(file))
