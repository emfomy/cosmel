#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os

import torch

from .model2c import Model2c
from .model2n import Model2n

class Model2cp(Model2c, Model2n):

	from .dataset import MentionProductDataSet as DataSet

	def __init__(self, meta):

		super().__init__(meta)

	def inputs(self, raws):

		# Combine inputs
		from .dataset import Inputs
		inputs = Inputs()
		inputs._2c = Model2c.inputs(raws[0])
		inputs._2n = Model2d.inputs(raws[1])
		return inputs

	def forward(self, inputs):

		text_loss = Model2c.forward(self, inputs._2c)
		name_loss = Model2n.forward(self, inputs._2n)

		return {**text_loss, **name_loss}
