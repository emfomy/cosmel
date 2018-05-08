#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import itertools
import os
import sys
import tqdm

import numpy as np

import torch
import torch.utils.data

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

	# Create dataset and dataloader
	inputs  = model.data(asmid_list)
	dataset = torch.utils.data.TensorDataset(*inputs)
	print(f'nun_train = {len(dataset)}')
	loader  = torch.utils.data.DataLoader(
		dataset=dataset,
		batch_size=32,
		shuffle=True,
		drop_last=True,
	)

	# Create optimizer
	optimizer = torch.optim.Adam(model.parameters())

	# Train
	num_epoch = 20
	num_step  = len(loader)

	for epoch in range(num_epoch):

		loss_sum = 0
		pbar = tqdm.trange(num_step, desc=f'Epoch {epoch+1:0{len(str(num_epoch))}}/{num_epoch}')
		pbar.set_postfix(loss=f'{0.:.6f}')
		for step, inputs in zip(pbar, loader):

			inputs_gpu = tuple(v.cuda() for v in inputs)

			label = inputs_gpu[-1]
			output = model(*inputs_gpu[:-1])
			loss = model.loss(output, label)
			loss_item = loss.item()
			loss_sum += loss_item

			pbar.set_postfix(loss=f'{loss_item:.6f}')

			optimizer.zero_grad()
			loss.backward()
			optimizer.step()

		pbar.set_postfix(loss=f'{loss_sum/num_step:.6f}')

	# Save models
	model.save(model_file)
	print(f'Saved training model into "{model_file}"')

	pass
