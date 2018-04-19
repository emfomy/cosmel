#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os

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

	def forward(self, **kwargs):

		text_1hot = kwargs['text_1hot']
		text_emb = self.text_encoder(**kwargs)
		text_softmax = torch.nn.functional.log_softmax(self.entity_emb(text_emb), dim=1)
		text_loss = -torch.mean(torch.bmm(text_softmax.unsqueeze(dim=1), text_1hot.unsqueeze(dim=2)))

		return {'text_loss': text_loss}

	def predict(self, **kwargs):

		text_emb     = self.text_encoder(**kwargs)
		text_softmax = torch.nn.functional.log_softmax(self.entity_emb(text_emb), dim=1)

		return text_softmax
