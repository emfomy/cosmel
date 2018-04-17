#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os

import torch

class Model2(torch.nn.Module):

	def __init__(self, meta):

		from model import ContextEncoder
		from model import DescriptionEncoder

		super().__init__()

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
		w2v_emb_size    = meta.keyed_vectors.vector_size
		print(f'w2v_emb_size  = {w2v_emb_size}')
		lstm_emb_size   = 100
		print(f'lstm_emb_size = {lstm_emb_size}')
		cnn_emb_size    = 100
		print(f'cnn_emb_size  = {cnn_emb_size}')
		cnn_win_size    = 5
		print(f'cnn_win_size  = {cnn_win_size}')

		# Create modules
		self.word_emb = torch.nn.Embedding(num_vocab, w2v_emb_size)
		self.word_emb.weight.data = torch.from_numpy(vocab_embedding)
		self.word_emb.weight.requires_grad = False

		self.text_encoder = ContextEncoder(meta, self.word_emb, lstm_emb_size)
		self.desc_encoder = DescriptionEncoder(meta, self.word_emb, cnn_emb_size, cnn_win_size)

		self.entity_emb = torch.nn.Linear(w2v_emb_size, num_label, bias=False)


	def forward(self, **kwargs):

		text_1hot = kwargs['text_1hot']
		desc_1hot = kwargs['desc_1hot']

		text_emb = self.text_encoder(**kwargs)
		desc_emb = self.desc_encoder(**kwargs)

		text_softmax = torch.nn.functional.log_softmax(self.entity_emb(text_emb), dim=1)
		desc_softmax = torch.nn.functional.log_softmax(self.entity_emb(desc_emb), dim=1)

		text_loss = -torch.mean(torch.bmm(text_softmax.unsqueeze(dim=1), text_1hot.unsqueeze(dim=2)))
		desc_loss = -torch.mean(torch.bmm(desc_softmax.unsqueeze(dim=1), desc_1hot.unsqueeze(dim=2)))

		return text_loss, desc_loss


	def predict(self, **kwargs):

		text_emb     = self.text_encoder(**kwargs)
		text_softmax = torch.nn.functional.log_softmax(self.entity_emb(text_emb), dim=1)

		return text_softmax

	def save(self, file):
		os.makedirs(os.path.dirname(file), exist_ok=True)
		torch.save(self.state_dict(), file)

	def load(self, file):
		self.load_state_dict(torch.load(file))
