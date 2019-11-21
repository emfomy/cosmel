#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <http://muyang.pro>'
__copyright__ = 'Copyright 2017-2018'

import os
import sys

import torch


class CoreData:

	def __init__(self, model):

		self.model  = model
		self.inputs = tuple()


class MentionData(CoreData):

	def __init__(self, model, ment_list, _all):

		super().__init__(model)

		self.repo, _   = model.meta.new_repo()
		self.corpus    = ment_list.corpus
		self.ment_list = ment_list

		# Load label
		raw_gid    = [m.gid for m in self.ment_list]
		gid        = model.label_encoder.transform(raw_gid, unknown=_all)
		self.label = torch.from_numpy(gid)


class ProductData(CoreData):

	def __init__(self, model):

		super().__init__(model)

		self.repo, self.prod_list = model.meta.new_repo()

		# Load label
		raw_pid    = [p.pid for p in self.prod_list]
		pid        = model.meta.p_encoder.transform(raw_pid)
		self.label = torch.from_numpy(pid)
