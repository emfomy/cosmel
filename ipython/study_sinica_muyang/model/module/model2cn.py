#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import numpy as np

import torch

from .model2c import Model2c
from .model2n import Model2n

class Model2cn(Model2c, Model2n):

	def __init__(self, meta):

		super().__init__(meta)

	def forward(self, pre_pad, post_pad, title_pad, rid_bag, brand_bag, name_pad):

		return \
			Model2c.forward(self, pre_pad, post_pad, title_pad, rid_bag, brand_bag) + \
			Model2n.forward(self, name_pad)

	def loss(self, text_prob, name_prob, ment_label, prod_label):

		text_loss = torch.nn.functional.cross_entropy(text_prob, ment_label)
		name_loss = torch.nn.functional.cross_entropy(name_prob, prod_label)

		return {'C': text_loss, 'N': name_loss}
