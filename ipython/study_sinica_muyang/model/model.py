#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os

import torch

from keras.preprocessing.sequence import pad_sequences
from sklearn.preprocessing import label_binarize

def lstm_size(module):
	return module.hidden_size * (module.bidirectional+1)

def cnn_size(module):
	return module.hidden_size


################################################################################################################################
# Context Encoder
#

class ContextEncoder(torch.nn.Module):

	def __init__(self, meta, word_emb_module, lstm_emb_size):

		super().__init__()

		# Set dimensions
		w2v_emb_size = word_emb_module.embedding_dim

		# Set size
		self.output_size = w2v_emb_size

		# Create modules
		self.local_encoder = LocalContextEncoder(meta, word_emb_module, lstm_emb_size)
		self.docu_encoder  = DocumentEncoder(meta, word_emb_module)

		self.linear = torch.nn.Linear(self.local_encoder.output_size + self.docu_encoder.output_size, self.output_size)

	def forward(self, **kwargs):

		local_emb = self.local_encoder(**kwargs)
		docu_emb  = self.docu_encoder(**kwargs)
		text_emb  = torch.nn.functional.relu(self.linear(torch.cat((local_emb, docu_emb), dim=1)))

		return text_emb


class LocalContextEncoder(torch.nn.Module):

	def __init__(self, meta, word_emb_module, lstm_emb_size):

		super().__init__()

		# Set dimensions
		w2v_emb_size = word_emb_module.embedding_dim

		# Set size
		self.output_size = w2v_emb_size

		# Create modules
		self.word_emb   = word_emb_module

		self.title_lstm = torch.nn.LSTM(w2v_emb_size, lstm_emb_size, batch_first=True, bidirectional=True)
		self.pre_lstm   = torch.nn.LSTM(w2v_emb_size, lstm_emb_size, batch_first=True)
		self.post_lstm  = torch.nn.LSTM(w2v_emb_size, lstm_emb_size, batch_first=True)

		lstm_cat_size  = lstm_size(self.title_lstm) + lstm_size(self.pre_lstm) + lstm_size(self.post_lstm)
		self.linear = torch.nn.Linear(lstm_cat_size, self.output_size)

	def forward(self, **kwargs):

		title_pad = kwargs['title_pad']
		pre_pad   = kwargs['pre_pad']
		post_pad  = kwargs['post_pad']

		title_pad_emb = self.word_emb(title_pad)
		pre_pad_emb   = self.word_emb(pre_pad)
		post_pad_emb  = self.word_emb(post_pad)

		title_lstm0, _ = self.title_lstm(title_pad_emb)
		pre_lstm0, _   = self.pre_lstm(pre_pad_emb)
		post_lstm0, _  = self.post_lstm(post_pad_emb)

		title_lstm = title_lstm0[:, -1, :]
		pre_lstm   = pre_lstm0[:, -1, :]
		post_lstm  = post_lstm0[:, -1, :]

		local_emb = torch.nn.functional.relu(self.linear(torch.cat((title_lstm, pre_lstm, post_lstm), dim=1)))

		return local_emb


class DocumentEncoder(torch.nn.Module):

	def __init__(self, meta, word_emb_module):

		super().__init__()

		# Get dimensions
		w2v_emb_size = word_emb_module.embedding_dim
		num_label    = len(meta.p_encoder.classes_)
		num_brand    = len(meta.b_encoder.classes_)

		# Set size
		self.output_size = w2v_emb_size

		# Create modules
		self.word_emb = word_emb_module

		self.linear = torch.nn.Linear(num_label+num_brand, self.output_size)

	def forward(self, **kwargs):

		pid_bag   = kwargs['pid_bag']
		brand_bag = kwargs['brand_bag']

		docu_emb = torch.nn.functional.relu(self.linear(torch.cat((pid_bag, brand_bag), dim=1)))

		return docu_emb


################################################################################################################################
# Description Encoder
#

class DescriptionEncoder(torch.nn.Module):

	def __init__(self, meta, word_emb_module, cnn_emb_size, cnn_win_size):

		super().__init__()

		# Get dimensions
		w2v_emb_size = word_emb_module.embedding_dim

		# Set size
		self.output_size = w2v_emb_size

		# Create modules
		self.word_emb = word_emb_module

		self.conv1d = torch.nn.Conv1d(w2v_emb_size, cnn_emb_size, cnn_win_size)
		self.linear = torch.nn.Linear(cnn_emb_size, w2v_emb_size)

	def forward(self, **kwargs):

		desc_pad = kwargs['desc_pad']

		desc_pad_emb = self.word_emb(desc_pad)
		desc_cnn     = self.conv1d(desc_pad_emb.permute(0, 2, 1))
		desc_pool    = torch.nn.functional.max_pool1d(desc_cnn, desc_cnn.size()[2]).squeeze_(2)
		desc_emb     = torch.nn.functional.relu(self.linear(desc_pool))

		return desc_emb

class ProductEncoder(torch.nn.Module):

	def __init__(self, info, word_emb_module):
		super().__init__()

		# Get dimensions
		w2v_emb_size = word_emb_module.embedding_dim

		# Set size
		self.output_size = w2v_emb_size

		# Create modules
		self.word_emb = word_emb_module

	def forward(self, **kwargs):
		
		product_pad = kwargs['product_pad']
		product_len = kwargs['product_len']

		product_pad_emb = self.word_emb(product_pad)
		product_sum = torch.sum(product_pad_emb, 0)
		product_avg = torch.mul(product_len, product_sum.t())


		return product_avg

