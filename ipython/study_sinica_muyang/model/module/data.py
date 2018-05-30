#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os
import sys

import torch

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from styleme import *

class CoreData:

	def __init__(self, model):

		self.model  = model
		self.inputs = tuple()


class MentionData(CoreData):

	def __init__(self, model, asmid_list, _all):

		super().__init__(model)

		parts       = list(set(m.aid for m in asmid_list))
		self.repo   = Repo(model.meta.repo_path)
		self.corpus = Corpus(model.meta.article_path, mention_root=model.meta.mention_path, parts=parts)

		self.ment_list = [self.corpus.id_to_mention[asmid.asmid] for asmid in asmid_list]
		for m, asmid in zip(self.ment_list, asmid_list):
			m.set_gid(asmid.gid)
			m.set_pid(asmid.pid)

		# Load label
		raw_gid    = [m.gid for m in self.ment_list]
		gid        = model.label_encoder.transform(raw_gid, unknown=_all)
		self.label = torch.from_numpy(gid)


class ProductData(CoreData):

	def __init__(self, model):

		super().__init__(model)

		self.repo = Repo(model.meta.repo_path)

		self.prod_list = list(self.repo.product_set)

		# Load label
		raw_pid    = [p.pid for p in self.prod_list]
		pid        = model.meta.p_encoder.transform(raw_pid)
		self.label = torch.from_numpy(pid)
