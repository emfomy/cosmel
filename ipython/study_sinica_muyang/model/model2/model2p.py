#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os

import torch

from .model2 import Model2

class Model2p(Model2):

	def __init__(self, meta):

		from .module import ProductEncoder

		super().__init__(meta)

		# Set dimensions
		cnn_emb_size = 100
		cnn_win_size = 2

		# Create modules
		self.prod_encoder = ProductEncoder(meta, self.word_emb, cnn_emb_size, cnn_win_size)

	def forward(self, **kwargs):

		prod_1hot = kwargs['desc_1hot']
		prod_emb = self.prod_encoder(**kwargs)
		prod_softmax = torch.nn.functional.log_softmax(self.entity_emb(prod_emb), dim=1)
		prod_loss = -torch.mean(torch.bmm(prod_softmax.unsqueeze(dim=1), prod_1hot.unsqueeze(dim=2)))

		return {'prod_loss': prod_loss}
