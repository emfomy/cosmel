#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os

import numpy as np

import torch

from .model2 import Model2

class Model2c(Model2):

	from .dataset import MentionDataSet as DataSet
	from .dataset import MentionDataSet as DataSetPredict

	def __init__(self, meta, xargs):

		import argparse
		parser = argparse.ArgumentParser(description='Model 2c')
		args, xargs_unk = parser.parse_known_args(xargs)

		from .module import ContextEncoder

		super().__init__(meta, xargs_unk)

		# Set dimensions
		lstm_emb_size = 100

		# Create modules
		self.text_encoder = ContextEncoder(meta, self.word_emb, lstm_emb_size)

	def inputs(self, raw):

		# Combine inputs
		from .dataset import Inputs
		inputs = Inputs()
		inputs._1hot = torch.autograd.Variable(torch.from_numpy(self.meta.p_binarizer.transform(raw.gid)).float())
		inputs.text  = self.text_encoder.inputs(raw)
		return inputs

	def forward(self, inputs):

		text_1hot    = inputs._1hot
		text_emb     = self.text_encoder(inputs.text)
		text_softmax = torch.nn.functional.log_softmax(self.entity_emb(text_emb), dim=1)
		text_loss    = -torch.mean(torch.bmm(text_softmax.unsqueeze(dim=1), text_1hot.unsqueeze(dim=2)))

		return {'text_loss': text_loss}

	def inputs_predict(self, raw):

		# Combine inputs
		from .dataset import Inputs
		inputs = Inputs()
		inputs._1hot = torch.autograd.Variable(torch.from_numpy(self.meta.p_binarizer.transform(raw.gid)).float())
		inputs.text  = self.text_encoder.inputs(raw)
		return inputs

	def predict(self, inputs):

		text_emb     = self.text_encoder(inputs.text)
		text_softmax = torch.nn.functional.log_softmax(self.entity_emb(text_emb), dim=1)
		pred_gid     = self.meta.p_encoder.inverse_transform(np.argmax(text_softmax.cpu().data.numpy(), axis=1))

		return pred_gid
