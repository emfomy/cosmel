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
from meta import *


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
		  choices=['model2c', 'model2cd', 'model2cn', 'model2cdn'], help='use model <model_type>')
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
		from module.model2c   import Model2c   as Model
	elif args.model == 'model2cd':
		from module.model2cd  import Model2cd  as Model
	elif args.model == 'model2cn':
		from module.model2cn  import Model2cp  as Model
	elif args.model == 'model2cdn':
		from module.model2cdn import Model2cdp as Model

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

	# Create model
	meta  = DatasetMeta.load(meta_file)
	model = Model(meta)
	model.cuda()
	print()
	print(model)
	print()

	# Load dataset
	asmid_list = AsmidList.load(data_file)
	dataset    = model.dataset(asmid_list)

	# Set batch size
	num_train = len(dataset)
	num_step  = num_train // 500
	print(f'num_train     = {num_train}')

	# Create optimizer
	optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()))

	# Train
	num_epoch = 20
	for epoch in range(num_epoch):

		for step, inputs in enumerate(dataset.batch(num_step)):

			# Forward and compute loss
			inputs.cuda()
			losses = model(inputs)
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
