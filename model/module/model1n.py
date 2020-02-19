#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <http://muyang.pro>'
__copyright__ = 'Copyright 2017-2018'

import numpy as np

import torch

from .model1 import Model1

class Model1n(Model1):

	class ProductData(Model1.ProductData):

		def __init__(self, model):

			super().__init__(model)

			self.inputs += model.name_encoder.data(self.prod_list, self.repo)

	def __init__(self, meta):

		from .module import NameEncoder

		super().__init__(meta)

		# Create modules
		self.name_encoder = NameEncoder(meta, self.word_emb)

		# Create label
		self.label_encoder = meta.p_encoder

	def forward(self, name_pad):

		name_emb  = self.name_encoder(name_pad)
		name_prob = self.entity_emb(name_emb)

		return (name_prob,)
