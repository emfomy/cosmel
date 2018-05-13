#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import numpy as np

import torch

from .model2 import Model2

class Model2c(Model2):

	class MentionData(Model2.MentionData):

		def __init__(self, model, asmid_list, _all):

			super().__init__(model, asmid_list, _all)

			self.inputs += model.text_encoder.data(self.ment_list, self.repo, self.corpus)

	def __init__(self, meta):

		from .module import ContextEncoder

		super().__init__(meta)

		# Set dimensions
		lstm_emb_size = 100

		# Create modules
		self.text_encoder = ContextEncoder(meta, self.word_emb, lstm_emb_size)

	def forward(self, pre_pad, post_pad, title_pad, pid_bag, brand_bag):

		text_emb  = self.text_encoder(pre_pad, post_pad, title_pad, pid_bag, brand_bag)
		text_prob = self.entity_emb(text_emb)

		return (text_prob,)

	def loss(self, text_prob, ment_label, prod_label):

		text_loss = torch.nn.functional.cross_entropy(text_prob, ment_label)
		return {'C': text_loss}

	def predict(self, *args):
		text_prob, = Model2c.forward(self, *args)
		return np.argmax(text_prob.cpu().data.numpy(), axis=1)
