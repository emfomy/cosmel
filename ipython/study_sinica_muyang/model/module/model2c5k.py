#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import numpy as np

import torch

from .model2c import Model2c

class Model2c5k(Model2c):

	def __init__(self, meta):

		super().__init__(meta)

		self.text_encoder.local_encoder.max_num_sentences = 5000
