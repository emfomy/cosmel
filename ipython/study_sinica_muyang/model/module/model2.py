#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os
import sys

import torch

from .model import Model

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

class Model2(Model):

	def __init__(self, meta):

		super().__init__(meta)

		num_label = len(meta.p_encoder.classes_)

		self.entity_emb = torch.nn.Linear(self.w2v_emb_size, num_label, bias=False)

		# Create label
		self.label_encoder = meta.p_encoder
