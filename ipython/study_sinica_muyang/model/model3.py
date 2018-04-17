#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__ = 'Chi-Yen Chen'
__email__ = 'jina199312@gmail.com'

import os
import numpy as np
import torch

from keras.preprocessing.sequence import pad_sequences
from sklearn.preprocessing import label_binarize

class Model3(torch.nn.Module):
	"""docstring for Model3"""
	def __init__(self, info):

		from model.model import ContextEncoder
		from model.model import DescriptionEncoder
		from model.model import ProductEncoder

		super().__init__()

		# Get sizes
		num_vocab = len(info.keyed_vectors.vocab)
		num_label = len(info.p_encoder.classes_)
		num_brand = len(info.b_encoder.classes_)
		print(f'num_vocab       = {num_vocab}')
		print(f'num_label       = {num_label}')
		print(f'num_brand       = {num_brand}')

		# Prepare embeddings
		vocab_embedding = info.keyed_vectors[info.keyed_vectors.index2word]
		vocab_embedding[0] = 0

		# Set dimensions
		w2v_emb_size    = info.keyed_vectors.vector_size
		print(f'w2v_emb_size    = {w2v_emb_size}')
		lstm_emb_size   = 100
		print(f'lstm_emb_size   = {lstm_emb_size}')
		cnn_emb_size    = 100
		print(f'cnn_emb_size    = {cnn_emb_size}')
		cnn_win_size    = 5
		print(f'cnn_win_size    = {cnn_win_size}')

		# Create modules
		self.word_emb = torch.nn.Embedding(num_vocab, w2v_emb_size)
		self.word_emb.weight.data = torch.from_numpy(vocab_embedding)
		self.word_emb.weight.requires_grad = False

		self.text_encoder = ContextEncoder(info, self.word_emb, lstm_emb_size)
		self.desc_encoder = DescriptionEncoder(info, self.word_emb, cnn_emb_size, cnn_win_size)

		self.product_encoder = ProductEncoder(info, self.word_emb)

	def forward(self, **kwargs):

		text_1hot = kwargs['text_1hot']
		desc_1hot = kwargs['desc_1hot']

		text_emb = self.text_encoder(**kwargs)
		desc_emb = self.desc_encoder(**kwargs)

		product_emb = self.product_encoder(**kwargs)

		text_softmax = torch.nn.functional.log_softmax(torch.matmul(text_emb, product_emb), dim=1)
		desc_softmax = torch.nn.functional.log_softmax(torch.matmul(desc_emb, product_emb), dim=1)

		text_loss = -torch.mean(torch.bmm(text_softmax.unsqueeze(dim=1), text_1hot.unsqueeze(dim=2)))
		desc_loss = -torch.mean(torch.bmm(desc_softmax.unsqueeze(dim=1), desc_1hot.unsqueeze(dim=2)))

		return text_loss, desc_loss

	def inputs(self, pack):

		class Inputs:

			def cuda(self):
				for k, v in vars(self).items():
					setattr(self, k, v.cuda())

		inputs = Inputs()

		post_code_re     = [list(reversed(l)) for l in pack.data.post_code]

		inputs.title_pad = torch.autograd.Variable(torch.from_numpy(pad_sequences(pack.data.title_code, padding='pre')).long().t())
		inputs.pre_pad   = torch.autograd.Variable(torch.from_numpy(pad_sequences(pack.data.pre_code,   padding='pre')).long().t())
		inputs.post_pad  = torch.autograd.Variable(torch.from_numpy(pad_sequences(post_code_re,         padding='post')).long().t())
		inputs.desc_pad  = torch.autograd.Variable(torch.from_numpy(pad_sequences(pack.info.desc_code,  padding='pre')).long().t())
		inputs.pid_bag   = torch.autograd.Variable(torch.from_numpy(pack.data.pid_bag).float())
		inputs.brand_bag = torch.autograd.Variable(torch.from_numpy(pack.data.brand_bag).float())
		inputs.text_1hot = torch.autograd.Variable(torch.from_numpy(label_binarize(pack.data.gid_code,
				range(len(pack.info.p_encoder.classes_)))).float())
		inputs.desc_1hot = torch.autograd.Variable(torch.from_numpy(label_binarize(pack.info.product_pid_code,
				range(len(pack.info.p_encoder.classes_)))).float())
		inputs.product_pad = torch.autograd.Variable(torch.from_numpy(pad_sequences(pack.info.product_code, padding='post')).long().t())
		inputs.product_len = torch.autograd.Variable(torch.from_numpy(np.asarray([1.0/len(x) if len(x)>0 else 0 for x in pack.info.product_code])).float())

		return inputs

	def predict(self, **kwargs):

		text_emb     = self.text_encoder(**kwargs)
		product_emb  = self.product_encoder(**kwargs)

		text_softmax = torch.nn.functional.log_softmax(torch.matmul(text_emb, product_emb), dim=1)

		return text_softmax

	def save(self, file):
		os.makedirs(os.path.dirname(file), exist_ok=True)
		torch.save(self.state_dict(), file)

	def load(self, file):
		self.load_state_dict(torch.load(file))
