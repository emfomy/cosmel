#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

################################################################################################################################
# Inputs
#
class Inputs:

	def cuda(self):
		for k, v in vars(self).items():
			setattr(self, k, v.cuda())
		return self

################################################################################################################################
# Raw Inputs
#
class Raw:
	pass


################################################################################################################################
# Core Data Set
#
class CoreDataSet:

	def __init__(self, model):

		self.model = model
		self.meta  = model.meta

	def __getitem__(self, idx):
		return self.model.inputs(self.raw(idx))

	def batch(self, num_step):

		batch_size = len(self) // num_step
		batch_idxs = np.split(np.random.permutation(len(self)), range(batch_size, len(self), batch_size))

		for _, idx in zip(range(num_step), batch_idxs):
			yield self[idx]


################################################################################################################################
# Mention Data Set
#
class MentionDataSet(CoreDataSet):

	def __init__(self, model, asmid_list):

		super().__init__(model)

		parts       = list(set(m.aid for m in asmid_list))
		self.repo   = Repo(self.meta.repo_path)
		self.corpus = Corpus(self.meta.article_path, self.meta.mention_path, parts=parts)

		self.mention_list = [self.corpus.id_to_mention[asmid.asmid] for asmid in asmid_list]
		for m in self.mention_list:
			if m.gid == 'NAP': m.set_gid('GP')
			if m.pid == 'NAP': m.set_pid('GP')
		for m, asmid in zip(self.mention_list, asmid_list):
			if not asmid.use_gid: m.set_gid(m.pid)

	def __len__(self):
		return len(self.mention_list)

	def raw(self, idx=None):

		if idx is None:
			sublist = np.asarray(self.mention_list)
		elif isinstance(idx, int):
			sublist = np.asarray([self.mention_list[idx]])
		else:
			sublist = np.asarray(self.mention_list)[idx]

		# Create Object
		retval = Raw()
		retval.repo    = self.repo
		retval.corpus  = self.corpus
		retval.sublist = sublist

		# Load Data
		retval.gid  = np.asarray([m.gid  for m in sublist])
		retval.pid  = np.asarray([m.pid  for m in sublist])
		retval.rule = np.asarray([m.rule for m in sublist])

		return retval


################################################################################################################################
# Product Data Set
#
class ProductDataSet(CoreDataSet):

	def __init__(self, model, asmid_list):

		super().__init__(model)

		self.repo = Repo(self.meta.repo_path)

		self.product_list = list(self.repo.product_set)

	def __len__(self):
		return len(self.product_list)

	def raw(self, idx=None):

		if idx is None:
			sublist = np.asarray(self.product_list)
		elif isinstance(idx, int):
			sublist = np.asarray([self.product_list[idx]])
		else:
			sublist = np.asarray(self.product_list)[idx]

		# Create object
		retval = Raw()
		retval.repo    = self.repo
		retval.sublist = sublist

		# Load Data
		retval.pid  = np.asarray([p.pid for p in sublist])

		return retval


################################################################################################################################
# Mantion & Product Data Set
#
class MentionProductDataSet(CoreDataSet):

	def __init__(self, model, asmid_list):

		super().__init__(model)

		self.mention_dataset = MentionDataSet(model, asmid_list)
		self.product_dataset = ProductDataSet(model, asmid_list)

	def __len__(self):
		return len(self.mention_dataset)

	def batch(self, num_step):
		return zip(self.mention_dataset.batch(num_step), self.product_dataset.batch(num_step))
