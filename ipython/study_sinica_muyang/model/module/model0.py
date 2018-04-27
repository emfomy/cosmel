#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os

import numpy as np

import torch

from sklearn.preprocessing import LabelEncoder

from .model import Model

class Model0(Model):

	from .dataset import MentionDataSet as DataSet

	def __init__(self, meta, xargs):

		import argparse
		parser = argparse.ArgumentParser(description='Model 0')
		args, xargs_unk = parser.parse_known_args(xargs)

		from .module import ContextEncoder

		super().__init__(meta, xargs_unk)

		# Set dimensions
		lstm_emb_size = 100

		# Prepare mention type encoder
		self.mtype_encoder = LabelEncoder()
		self.mtype_encoder.fit(['PID', 'OSP', 'GP'])

		# Create modules
		self.local_encoder = ContextEncoder(meta, self.word_emb, lstm_emb_size)
		self.linear1       = torch.nn.Linear(self.local_encoder.output_size, 100)
		self.linear2       = torch.nn.Linear(100, len(self.mtype_encoder.classes_))

	def inputs(self, raw):

		# Combine inputs
		from .dataset import Inputs
		inputs = Inputs()
		inputs.label = torch.autograd.Variable(torch.from_numpy(self.mtype_encoder.transform(raw.gid)).long())
		inputs.local = self.local_encoder.inputs(raw)
		return inputs

	def forward(self, inputs):

		mtype_label   = inputs.label
		local_emb     = self.local_encoder(inputs.local)
		mtype_prob    = self.linear2(self.linear1(local_emb).clamp(min=0))
		local_loss    = torch.nn.functional.cross_entropy(mtype_prob, mtype_label)

		return {'local_loss': local_loss}

	def predict(self, inputs):

		local_emb     = self.local_encoder(inputs.local)
		mtype_prob    = self.linear2(self.linear1(local_emb).clamp(min=0))
		pred_mtype    = self.mtype_encoder.inverse_transform(np.argmax(mtype_prob.cpu().data.numpy(), axis=1))

		return pred_mtype
