#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os

import torch

from .model2 import Model2

class Model2n(Model2):

	from .dataset import ProductDataSet as DataSet

	def __init__(self, meta):

		from .module import NameEncoder

		super().__init__(meta)

		# Set dimensions
		cnn_emb_size = 100
		cnn_win_size = 2

		# Create modules
		self.name_encoder = NameEncoder(meta, self.word_emb, cnn_emb_size, cnn_win_size)

	def inputs(self, raw):

		# Combine inputs
		from .dataset import Inputs
		inputs = Inputs()
		inputs._1hot = torch.autograd.Variable(torch.from_numpy(self.meta.p_binarizer.transform(raw.pid)).float())
		inputs.name  = self.name_encoder.inputs(raw)
		return inputs

	def forward(self, inputs):

		name_1hot = inputs._1hot
		name_emb  = self.name_encoder(inputs.name)
		name_softmax = torch.nn.functional.log_softmax(self.entity_emb(name_emb), dim=1)
		name_loss = -torch.mean(torch.bmm(name_softmax.unsqueeze(dim=1), name_1hot.unsqueeze(dim=2)))

		return {'name_loss': name_loss}
