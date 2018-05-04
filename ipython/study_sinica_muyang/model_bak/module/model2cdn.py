#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os

import torch

from .model2c import Model2c
from .model2d import Model2d
from .model2n import Model2n

class Model2cdn(Model2c, Model2d, Model2n):

	from .dataset import MentionProductDataSet as DataSet

	def __init__(self, meta, xargs):

		import argparse
		parser = argparse.ArgumentParser(description='Model 2cdn')
		args, xargs_unk = parser.parse_known_args(xargs)

		super().__init__(meta, xargs_unk)

	def inputs(self, raws):

		# Combine inputs
		from .dataset import Inputs
		inputs = Inputs()
		inputs._2c = Model2c.inputs(self, raws[0])
		inputs._2d = Model2d.inputs(self, raws[1])
		inputs._2n = Model2d.inputs(self, raws[1])
		return inputs

	def forward(self, inputs):

		text_loss = Model2c.forward(self, inputs._2c)
		desc_loss = Model2d.forward(self, inputs._2d)
		name_loss = Model2n.forward(self, inputs._2n)

		return {**text_loss, **desc_loss, **name_loss}