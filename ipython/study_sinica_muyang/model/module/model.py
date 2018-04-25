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
		num_vocab = len(meta.keyed_vectors.vocab)

		# Prepare embeddings
		vocab_embedding = meta.keyed_vectors[meta.keyed_vectors.index2word]
		vocab_embedding[0] = 0

		# Set dimensions
		self.w2v_emb_size = meta.keyed_vectors.vector_size

		# Create modules
		self.word_emb = torch.nn.Embedding(num_vocab, self.w2v_emb_size)
		self.word_emb.weight.data = torch.from_numpy(vocab_embedding)
		# self.word_emb.weight.requires_grad = False

	def dataset(self, asm_list):
		return self.DataSet(self, asm_list)

	def save(self, file):
		os.makedirs(os.path.dirname(file), exist_ok=True)
		torch.save(self.state_dict(), file)

	def load(self, file):
		self.load_state_dict(torch.load(file))
