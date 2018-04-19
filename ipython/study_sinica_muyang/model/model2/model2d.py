#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os

import torch

from .model2 import Model2

class Model2d(Model2):

	def __init__(self, meta):

		from .module import DescriptionEncoder

		super().__init__(meta)

		# Set dimensions
		cnn_emb_size = 100
		cnn_win_size = 5

		# Create modules
		self.desc_encoder = DescriptionEncoder(meta, self.word_emb, cnn_emb_size, cnn_win_size)

	def forward(self, **kwargs):

		desc_1hot = kwargs['desc_1hot']
		desc_emb = self.desc_encoder(**kwargs)
		desc_softmax = torch.nn.functional.log_softmax(self.entity_emb(desc_emb), dim=1)
		desc_loss = -torch.mean(torch.bmm(desc_softmax.unsqueeze(dim=1), desc_1hot.unsqueeze(dim=2)))

		return {'desc_loss': desc_loss}
