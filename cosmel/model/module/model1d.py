#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import numpy as np

import torch

from .model1 import Model1

class Model1d(Model1):

	class ProductData(Model1.ProductData):

		def __init__(self, model):

			super().__init__(model)

			self.inputs += model.desc_encoder.data(self.prod_list, self.repo)

	def __init__(self, meta):

		from .module import DescriptionEncoder

		super().__init__(meta)

		# Set dimensions
		cnn_emb_size = 100
		cnn_win_size = 5

		# Create modules
		self.desc_encoder = DescriptionEncoder(meta, self.word_emb, cnn_emb_size, cnn_win_size)

		# Create label
		self.label_encoder = meta.p_encoder

	def forward(self, desc_pad):

		desc_emb  = self.desc_encoder(desc_pad)
		desc_prob = self.entity_emb(desc_emb)

		return (desc_prob,)
