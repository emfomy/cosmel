#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import itertools
import math
import os
import sys
import tqdm

import numpy as np

import torch
import torch.utils.data

from sklearn.metrics import accuracy_score

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from styleme import *
from model.module.meta import *


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
			help='use model <model_type>')
	argparser.add_argument('--meta', metavar='<meta_name>', \
			help='dataset meta path; default is "[<dir>/]meta.pkl"')

	argparser.add_argument('-c', '--check', action='store_true', help='Check arguments')

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

	model_pkg_name = args.model
	model_cls_name = args.model.capitalize()
	Model = getattr(__import__('module.'+model_pkg_name, fromlist=model_cls_name), model_cls_name)

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

	############################################################################################################################
	# Initialize model
	#

	# Load data
	meta       = DataSetMeta.load(meta_file)
	asmid_list = AsmidList.load(data_file)

	# Create model
	model = Model(meta)
	model.cuda()
	print()
	print(model)
	print()

	# Load pretrained model
	if pretrain_file:
		model.load(pretrain_file)
		print(f'Loaded pretrained model from "{pretrain_file}"')
		print()

	############################################################################################################################
	# Load data
	#

	# Create mention dataset and dataloader
	ment_data    = model.ment_data(asmid_list)
	ment_dataset = torch.utils.data.TensorDataset(*ment_data.inputs, ment_data.label)
	print(f'#mention = {len(ment_dataset)}')
	ment_loader  = torch.utils.data.DataLoader(
		dataset=ment_dataset,
		batch_size=32,
		shuffle=True,
		drop_last=(len(ment_dataset) >= 32),
	)

	# Create product dataset and dataloader
	prod_data    = model.prod_data()
	prod_dataset = torch.utils.data.TensorDataset(*prod_data.inputs, prod_data.label)
	print(f'#product = {len(prod_dataset)}')
	prod_loader  = torch.utils.data.DataLoader(
		dataset=prod_dataset,
		batch_size=max(1, math.ceil(len(prod_dataset) / len(ment_loader))),
		shuffle=True,
		drop_last=True,
	)

	assert(len(ment_loader) >= len(prod_loader))

	############################################################################################################################
	# Training
	#

	# Create optimizer
	optimizer = torch.optim.Adam(model.parameters())
	num_epoch = 10
	num_step  = len(ment_loader)

	from collections import defaultdict

	for epoch in range(num_epoch):

		# Training
		losses_sum = defaultdict(lambda: 0.)
		pbar = tqdm.trange(num_step, desc=f'Epoch {epoch+1:0{len(str(num_epoch))}}/{num_epoch}')
		pbar.set_postfix(loss=f'{0.:09.6f}')
		for step, ment_inputs_cpu, prod_inputs_cpu in zip(pbar, ment_loader, itertools.cycle(prod_loader)):

			inputs  = tuple(v.cuda() for v in itertools.chain(ment_inputs_cpu[:-1], prod_inputs_cpu[:-1]))
			labels  = (ment_inputs_cpu[-1].cuda(), prod_inputs_cpu[-1].cuda())
			outputs = model(*inputs)

			losses  = model.loss(*outputs, *labels)
			loss    = sum(losses.values())

			losses_sum['*loss'] += loss.item()
			for k, v in losses.items():
				losses_sum[k] += v.item()

			postfix = {k: f'{v/(step+1):09.6f}' for k, v in losses_sum.items()}
			pbar.set_postfix(**postfix)

			optimizer.zero_grad()
			loss.backward()
			optimizer.step()

	# Save models
	model.save(model_file)
	print(f'Saved training model into "{model_file}"')

	pass
