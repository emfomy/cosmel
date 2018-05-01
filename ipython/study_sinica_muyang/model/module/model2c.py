#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os
import sys

import numpy as np

import torch

from .model2 import Model2

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

class Model2c(Model2):

	def __init__(self, meta):

		from .module import ContextEncoder

		super().__init__(meta)

		# Set dimensions
		lstm_emb_size = 100

		# Create modules
		self.text_encoder = ContextEncoder(meta, self.word_emb, lstm_emb_size)

	def data(self, asmid_list):

		asmid_list.filter_sp()

		parts  = list(set(m.aid for m in asmid_list))
		repo   = Repo(self.meta.repo_path)
		corpus = Corpus(self.meta.article_path, self.meta.mention_path, parts=parts)

		ment_list = [corpus.id_to_mention[asmid.asmid] for asmid in asmid_list]
		for m, asmid in zip(ment_list, asmid_list):
			m.set_gid(asmid.gid)
			m.set_pid(asmid.pid)

		# Load label
		raw_gid = [m.gid for m in ment_list]
		gid     = self.meta.p_encoder.transform(raw_gid)
		gid_var = torch.from_numpy(gid)

		return self.text_encoder.data(ment_list, repo, corpus) + (gid_var,)

	def forward(self, title_pad, pre_pad, post_pad, pid_bag, brand_bag):

		text_emb  = self.text_encoder(title_pad, pre_pad, post_pad, pid_bag, brand_bag)
		text_prob = self.entity_emb(text_emb)

		return text_prob

	def loss(self, text_prob, label):
		return torch.nn.functional.cross_entropy(text_prob, label)

	def predict(self, text_prob):
		return np.argmax(text_prob.cpu().data.numpy(), axis=1)
