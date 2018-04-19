#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import argparse
import os
import sys

import numpy as np

import torch
import torch.utils.data
from torch.nn.utils.rnn import pack_padded_sequence

sys.path.insert(0, os.path.abspath('.'))
from styleme import *
from data import *

class Inputs:

	def __init__(self, **kwargs):
		for k, v in kwargs.items():
			setattr(self, k, torch.autograd.Variable(v))

	def cuda(self):
		for k, v in vars(self).items():
			setattr(self, k, v.cuda())


if __name__ == '__main__':

	# Parse arguments
	argparser = argparse.ArgumentParser(description='Train StyleMe model.')

	arggroup = argparser.add_mutually_exclusive_group()
	arggroup.add_argument('-v', '--ver', metavar='<ver>#<date>', \
			help='set <dir> as "result/<ver>_<date>"')
	arggroup.add_argument('-D', '--dir', metavar='<dir>', \
			help='prepend <dir> to data and model path')

	argparser.add_argument('-d', '--data', metavar='<data_name>', required=True, \
			help='training data path; load data list from "[<dir>/]<data_name>.list.txt"')
	argparser.add_argument('-w', '--weight', metavar='<weight_name>', required=True, \
			help='output weight path; output model weight into "[<dir>/]<weight_name>.<model_type>.weight.pt"')
	argparser.add_argument('-p', '--pretrain', metavar='<pretrained_name>', \
			help='pretrained weight path; load model weight from "[<dir>/]<pretrained_name>.weight.pt"')
	argparser.add_argument('-m', '--model', metavar='<model_type>', required=True, \
		  choices=['model2c', 'model2cd', 'model2cp', 'model2cdp'], help='use model <model_type>')
	argparser.add_argument('--meta', metavar='<meta_name>', \
			help='dataset meta path; default is "[<dir>/]meta.pkl"')

	argparser.add_argument('-c', '--check', action='store_true', help='Check arguments.')

	args = argparser.parse_args()

	vers          = args.ver.split('#')
	ver           = vers[0]
	date          = ''
	if len(vers) > 1:
		date        = f'_{vers[1]}'

	result_root = ''
	if args.ver != None:
		result_root = f'result/{ver}{date}/'
	if args.dir != None:
		result_root = f'{args.dir}/'

	data_file     = f'{result_root}{args.data}.list.txt'
	model_file    = f'{result_root}{args.weight}.{args.model}.pt'

	pretrain_file = ''
	if args.pretrain != None:
		pretrain_file = f'{result_root}{args.pretrain}.{args.model}.pt'

	meta_file     = f'{result_root}meta.pkl'
	if args.meta != None:
		meta_file = args.meta

	if   args.model == 'model2c':
		from model2.model2c   import Model2c   as Model
	elif args.model == 'model2cd':
		from model2.model2cd  import Model2cd  as Model
	elif args.model == 'model2cp':
		from model2.model2cp  import Model2cp  as Model
	elif args.model == 'model2cdp':
		from model2.model2cdp import Model2cdp as Model

	# Print arguments
	print()
	print(args)
	print()
	print(f'model         = {args.model}')
	print(f'data_file     = {data_file}')
	print(f'model_file    = {model_file}')
	print(f'pretrain_file = {pretrain_file}')
	print(f'meta_file     = {meta_file}')
	print()

	if args.check: exit()

	# Load data
	meta         = DatasetMeta.load(meta_file)
	asmid_list   = AsmidList.load(data_file)
	text_dataset = MentionDataset(meta, asmid_list)
	desc_dataset = ProductDataset(meta)
	num_train    = len(text_dataset)
	print(f'num_train     = {num_train}')

	# Set batch size
	num_text        = len(text_dataset)
	num_desc        = len(desc_dataset)
	text_batch_size = 500
	num_step        = num_text // text_batch_size
	desc_batch_size = num_desc // num_step

	# Create model
	model = Model(meta)
	model.cuda()
	print()
	print(model)
	print()

	# Create optimizer
	optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()))

	# Train
	num_epoch = 20
	for epoch in range(num_epoch):

		text_batch_idxs = np.split(np.random.permutation(num_text), range(text_batch_size, num_text, text_batch_size))
		desc_batch_idxs = np.split(np.random.permutation(num_desc), range(desc_batch_size, num_desc, desc_batch_size))

		for step, text_batch_idx, desc_batch_idx in zip(range(num_step), text_batch_idxs, desc_batch_idxs):
			text_batch = text_dataset[text_batch_idx]
			desc_batch = desc_dataset[desc_batch_idx]

			inputs = Inputs(**text_batch, **desc_batch)
			inputs.cuda()

			# Forward and compute loss
			losses = model(**vars(inputs))
			loss = sum(losses.values())
			printr( \
					f'Epoch: {epoch+1:0{len(str(num_epoch))}}/{num_epoch}' + \
					f' | Batch: {step+1:0{len(str(num_step))}}/{num_step}' + \
					f' | loss: {loss.data[0]:.6f}' + \
					''.join([f' | {k}: {v.data[0]:.6f}' for k, v in losses.items()]))
			sys.stdout.flush()

			optimizer.zero_grad()
			loss.backward()
			optimizer.step()

		print()

	# Save models
	model.save(model_file)
	print(f'Saved training model into "{model_file}"')

	pass
