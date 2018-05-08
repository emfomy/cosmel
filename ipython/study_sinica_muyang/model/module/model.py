#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os

import torch

class Model(torch.nn.Module):

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

	def data(self, asmid_list):
		raise NotImplementedError

	def data_predict(self, asmid_list):
		return self.data(asmid_list)

	def data_predict_all(self, asmid_list):
		return self.data(asmid_list)

	def save(self, file):
		os.makedirs(os.path.dirname(file), exist_ok=True)
		torch.save(self.state_dict(), file)

	def load(self, file):
		self.load_state_dict(torch.load(file))
