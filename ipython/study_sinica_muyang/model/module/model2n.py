#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import numpy as np

import torch

from .model2 import Model2

class Model2n(Model2):

	class ProductData(Model2.ProductData):

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
