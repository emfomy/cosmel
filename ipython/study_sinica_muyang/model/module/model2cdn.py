#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import numpy as np

import torch

from .model2c import Model2c
from .model2d import Model2d
from .model2n import Model2n

class Model2cdn(Model2c, Model2d, Model2n):

	class ProductData(Model2d.ProductData, Model2n.ProductData):
		pass

	def __init__(self, meta):

		super().__init__(meta)

	def forward(self, pre_pad, post_pad, title_pad, pid_bag, brand_bag, desc_pad, name_pad):

		return \
			Model2c.forward(self, pre_pad, post_pad, title_pad, pid_bag, brand_bag) + \
			Model2d.forward(self, desc_pad) + \
			Model2n.forward(self, name_pad)

	def loss(self, text_prob, desc_prob, name_prob, ment_label, prod_label):

		text_loss = torch.nn.functional.cross_entropy(text_prob, ment_label)
		desc_loss = torch.nn.functional.cross_entropy(desc_prob, prod_label)
		name_loss = torch.nn.functional.cross_entropy(name_prob, prod_label)

		return {'C': text_loss, 'D': desc_loss, 'N': name_loss}
