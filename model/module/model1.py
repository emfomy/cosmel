#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <http://muyang.pro>'
__copyright__ = 'Copyright 2017-2018'

import os
import sys

import torch

from .model import Model

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *

class Model1(Model):

	def __init__(self, meta):

		super().__init__(meta)

		num_label = len(meta.p_encoder.classes_)

		self.entity_emb = torch.nn.Linear(self.w2v_emb_size, num_label, bias=False)

		# Create label
		self.label_encoder = meta.p_encoder
