#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os
import sys

import numpy as np

import torch

from .model import Model
from .meta import LabelEncoder

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *

class Model0(Model):

	class MentionData(Model.MentionData):

		def __init__(self, model, asmid_list, _all):

			asmid_list.gid_to_mtype()

			super().__init__(model, asmid_list, _all)

			self.inputs += model.text_encoder.data(self.ment_list, self.repo, self.corpus)

	def __init__(self, meta):

		from .module import ContextEncoder

		super().__init__(meta)

		# Set dimensions
		lstm_emb_size = 100

		# Prepare mention type encoder
		self.label_encoder = LabelEncoder()
		self.label_encoder.fit(['PID', 'OSP', 'GP'])

		# Create modules
		self.text_encoder = ContextEncoder(meta, self.word_emb, lstm_emb_size)
		text_size   = self.text_encoder.output_size
		label_size  = len(self.label_encoder.classes_)
		self.linear = torch.nn.Linear(text_size, label_size)

	def forward(self, title_pad, pre_pad, post_pad, pid_bag, brand_bag):

		text_emb   = self.text_encoder(title_pad, pre_pad, post_pad, pid_bag, brand_bag)
		mtype_prob = self.linear(text_emb)

		return (mtype_prob,)

	def loss(self, mtype_prob, mtype_label, prod_label):
		mtype_loss = torch.nn.functional.cross_entropy(mtype_prob, mtype_label)
		return {'0': mtype_loss}

	def predict(self, *args):
		mtype_prob, = Model0.forward(self, *args)
		return np.argmax(mtype_prob.cpu().data.numpy(), axis=1)
