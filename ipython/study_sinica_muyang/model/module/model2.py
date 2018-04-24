#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os

import torch

from .model import Model

class Model2(Model):

	def __init__(self, meta):

		super().__init__(meta)

		num_label = len(meta.p_encoder.classes_)

		self.entity_emb = torch.nn.Linear(self.w2v_emb_size, num_label, bias=False)
