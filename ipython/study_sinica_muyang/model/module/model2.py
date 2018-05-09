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

	def _data(self, asmid_list, sp=True):

		if sp:
			asmid_list.filter_sp()

		parts  = list(set(m.aid for m in asmid_list))
		repo   = Repo(self.meta.repo_path)
		corpus = Corpus(self.meta.article_path, mention_root=self.meta.mention_path, parts=parts)

		ment_list = [corpus.id_to_mention[asmid.asmid] for asmid in asmid_list]
		for m, asmid in zip(ment_list, asmid_list):
			m.set_gid(asmid.gid)
			m.set_pid(asmid.pid)

		# Load label
		raw_gid = [m.gid for m in ment_list]
		gid = self.meta.p_encoder.transform(raw_gid, unknown=(not sp))
		gid_var = torch.from_numpy(gid)

		return ment_list, repo, corpus, gid_var
