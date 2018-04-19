#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os

import torch

from .model2c import Model2c
from .model2p import Model2p

class Model2cp(Model2c, Model2p):

	def __init__(self, meta):

		super().__init__(meta)

	def forward(self, **kwargs):

		text_loss = Model2c.forward(self, **kwargs)
		prod_loss = Model2p.forward(self, **kwargs)

		return {**text_loss, **prod_loss}
