#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os
import sys

import numpy as np

import torch

from .model import Model

from sklearn.preprocessing import LabelEncoder

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

class Model0(Model):

	def __init__(self, meta):

		from .module import ContextEncoder

		super().__init__(meta)

		# Set dimensions
		lstm_emb_size = 100

		# Prepare mention type encoder
		self.label_encoder = LabelEncoder()
		self.label_encoder.fit(['PID', 'OSP', 'GP'])

		# Create modules
		self.text_encoder = ContextEncoder(meta, self.word_emb, lstm_emb_size)
		self.linear1       = torch.nn.Linear(self.text_encoder.output_size, 100)
		self.linear2       = torch.nn.Linear(100, len(self.label_encoder.classes_))

	def data(self, asmid_list):

		asmid_list.gid_to_mtype()

		parts  = list(set(m.aid for m in asmid_list))
		repo   = Repo(self.meta.repo_path)
		corpus = Corpus(self.meta.article_path, self.meta.mention_path, parts=parts)

		ment_list = [corpus.id_to_mention[asmid.asmid] for asmid in asmid_list]
		for m, asmid in zip(ment_list, asmid_list):
			m.set_gid(asmid.gid)
			m.set_pid(asmid.pid)
		for m in ment_list:
			if m.gid == 'NAP': m.set_gid('GP')
			if m.pid == 'NAP': m.set_pid('GP')

		# Load label
		raw_gid = [m.gid for m in ment_list]
		gid     = self.label_encoder.transform(raw_gid)
		gid_var = torch.from_numpy(gid)

		return self.text_encoder.data(ment_list, repo, corpus) + (gid_var,)

	def forward(self, title_pad, pre_pad, post_pad, pid_bag, brand_bag):

		text_emb   = self.text_encoder(title_pad, pre_pad, post_pad, pid_bag, brand_bag)
		mtype_prob = self.linear2(self.linear1(text_emb).clamp(min=0))

		return mtype_prob

	def loss(self, mtype_prob, label):
		return torch.nn.functional.cross_entropy(mtype_prob, label)

	def predict(self, mtype_prob):
		return np.argmax(mtype_prob.cpu().data.numpy(), axis=1)
