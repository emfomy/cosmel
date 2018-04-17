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
from model2 import Model2 as Model

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
			help='append extensions to data and model path; use ".data.pkl" for data, ".weight.pt" for weight.')

	argparser.add_argument('-d', '--data', metavar='<data_name>', required=True, \
			help='training data path; load data list from "[<dir>/]<data_name>.list.txt"')
	argparser.add_argument('-w', '--weight', metavar='<weight_name>', required=True, \
			help='output weight path; output model weight into "[<dir>/]<weight_name>.weight.pt", '+ \
				'and predicting model into "[<dir>/]<model_name>.predict.model"')
	argparser.add_argument('-p', '--pretrain', metavar='<pretrained_name>', \
			help='pretrained weight path; load model weight from "[<dir>/]<pretrained_name>.weight.pt"')
	argparser.add_argument('-m', '--model', metavar='<model_name>', choices=['model2', 'model3'], \
			help='use model from <model_name>')
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
	model_file    = f'{result_root}{args.weight}.weight.pt'

	pretrain_file = ''
	if args.pretrain != None:
		pretrain_file = f'{result_root}{args.pretrain}.weight.pt'

	if args.model == 'model2':
		from model2 import Model2 as Model
	elif args.model == 'model3':
		from model3 import Model3 as Model

	meta_file     = f'{result_root}meta.pkl'
	if args.meta != None:
		meta_file = args.meta

	# Print arguments
	print()
	print(args)
	print()
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
	batch_size = 500

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

		text_idxs = np.split(np.random.permutation(num_train), range(batch_size, num_train, batch_size))

		num_step = len(text_idxs)
		for step, text_idx in enumerate(text_idxs):
			text_batch = text_dataset[text_idx]
			desc_batch = desc_dataset[:]

			inputs = Inputs(**text_batch, **desc_batch)
			inputs.cuda()

			# Forward and compute loss
			text_loss, desc_loss = model(**vars(inputs))
			loss  = text_loss + desc_loss

			loss_data      = loss.data[0]
			text_loss_data = text_loss.data[0]
			desc_loss_data = desc_loss.data[0]
			printr(f'Epoch: {epoch+1:0{len(str(num_epoch))}}/{num_epoch} | Batch: {step+1:0{len(str(num_step))}}/{num_step}' + \
					f' | loss: {loss_data:.6f} | text_loss: {text_loss_data:.6f} | desc_loss: {desc_loss_data:.6f}')
			sys.stdout.flush()

			optimizer.zero_grad()
			loss.backward()
			optimizer.step()

		print()

	# Save models
	model.save(model_file)
	print(f'Saved training model into "{model_file}"')

	pass
