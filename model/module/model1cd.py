#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <http://muyang.pro>'
__copyright__ = 'Copyright 2017-2018'

import numpy as np

import torch

from .model1c import Model1c
from .model1d import Model1d

class Model1cd(Model1c, Model1d):

	def __init__(self, meta):

		super().__init__(meta)

	def forward(self, pre_pad, post_pad, title_pad, rid_bag, brand_bag, desc_pad):

		return \
			Model1c.forward(self, pre_pad, post_pad, title_pad, rid_bag, brand_bag) + \
			Model1d.forward(self, desc_pad)

	def loss(self, text_prob, desc_prob, ment_label, prod_label):

		text_loss = torch.nn.functional.cross_entropy(text_prob, ment_label)
		desc_loss = torch.nn.functional.cross_entropy(desc_prob, prod_label)

		return {'C': text_loss, 'D': desc_loss}
