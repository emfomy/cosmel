#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os

import torch

from .model import Model

class Model2(Model):

	def __init__(self, meta):

		super().__init__(meta)

		# Get sizes
		num_vocab = len(meta.keyed_vectors.vocab)
		num_label = len(meta.p_encoder.classes_)
		num_brand = len(meta.b_encoder.classes_)
		print(f'num_vocab     = {num_vocab}')
		print(f'num_label     = {num_label}')
		print(f'num_brand     = {num_brand}')

		# Prepare embeddings
		vocab_embedding = meta.keyed_vectors[meta.keyed_vectors.index2word]
		vocab_embedding[0] = 0

		# Set dimensions
		w2v_emb_size  = meta.keyed_vectors.vector_size

		# Create modules
		self.word_emb = torch.nn.Embedding(num_vocab, w2v_emb_size)
		self.word_emb.weight.data = torch.from_numpy(vocab_embedding)
		# self.word_emb.weight.requires_grad = False

		self.entity_emb = torch.nn.Linear(w2v_emb_size, num_label, bias=False)
