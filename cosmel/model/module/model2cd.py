#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import numpy as np

import torch

from .model2c import Model2c
from .model2d import Model2d

class Model2cd(Model2c, Model2d):

	def __init__(self, meta):

		super().__init__(meta)

	def forward(self, pre_pad, post_pad, title_pad, rid_bag, brand_bag, desc_pad):

		return \
			Model2c.forward(self, pre_pad, post_pad, title_pad, rid_bag, brand_bag) + \
			Model2d.forward(self, desc_pad)

	def loss(self, text_prob, desc_prob, ment_label, prod_label):

		text_loss = torch.nn.functional.cross_entropy(text_prob, ment_label)
		desc_loss = torch.nn.functional.cross_entropy(desc_prob, prod_label)

		return {'C': text_loss, 'D': desc_loss}
