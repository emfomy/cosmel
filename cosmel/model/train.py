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

from cosmel import *
from model.module.meta import *


if __name__ == '__main__':

	# Parse arguments
	argparser = argparse.ArgumentParser(description='Train CosmEL model.')

	arggroup = argparser.add_mutually_exclusive_group()
	arggroup.add_argument('-v', '--ver', metavar='<ver>#<date>', \
			help='set <dir> as "data/<ver>/model/<date>"')
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
	argparser.add_argument('-e', '--epoch', metavar='<num_epoch>', type=int, default=10, \
			help='train <num_epoch> times; default is 10')
	argparser.add_argument('--test_size', metavar='<test_size>', type=float, default=0.3, \
			help='split <test_size> mentions for testing; default is 0.3')

	argparser.add_argument('-c', '--check', action='store_true', help='Check arguments')

	args = argparser.parse_args()

	vers = args.ver.split('#')
	assert len(vers) == 2, argparser.format_usage()
	ver  = vers[0]
	date = vers[1]

	data_root = f'data/{ver}'

	result_root = ''
	if args.ver != None:
		result_root = f'{data_root}/model/{date}'
	if args.dir != None:
		result_root = f'{args.dir}'

	data_file     = f'{result_root}/{args.data}.list.txt'
	model_file    = f'{result_root}/{args.weight}.{args.model}.pt'

	pretrain_file = ''
	if args.pretrain != None:
		pretrain_file = f'{result_root}/{args.pretrain}.{args.model}.pt'

	meta_file     = f'{result_root}/meta.pkl'
	if args.meta != None:
		meta_file = args.meta

	num_epoch = args.epoch
	test_size = args.test_size

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
	print(f'num_epoch     = {num_epoch}')
	print(f'test_size     = {test_size}')
	print()

	if args.check: exit()

	############################################################################################################################
	# Initialize model
	#

	# Load data
	meta       = DataSetMeta.load(meta_file)
	asmid_list = AsmidList.load(data_file)

	train_asmid_list, test_asmid_list = asmid_list.train_test_split(test_size=test_size, random_state=0, shuffle=True)

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
	# Load training data
	#

	# Create training mention dataset and dataloader
	ment_data    = model.ment_data(train_asmid_list)
	ment_dataset = torch.utils.data.TensorDataset(*ment_data.inputs, ment_data.label)
	print(f'#train_mention = {len(ment_dataset)}')
	ment_loader  = torch.utils.data.DataLoader(
		dataset=ment_dataset,
		batch_size=32,
		shuffle=True,
		drop_last=(len(ment_dataset) >= 32),
	)

	# Create training product dataset and dataloader
	prod_data    = model.prod_data()
	prod_dataset = torch.utils.data.TensorDataset(*prod_data.inputs, prod_data.label)
	print(f'#train_product = {len(prod_dataset)}')
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
			if len(losses.items()) > 1:
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
	print()

	############################################################################################################################
	# Load testing data
	#

	# Create testing mention dataset and dataloader
	test_data    = model.ment_data(test_asmid_list)
	test_dataset = torch.utils.data.TensorDataset(*test_data.inputs)
	print(f'#test_mention = {len(test_dataset)}')
	test_loader  = torch.utils.data.DataLoader(
		dataset=test_dataset,
		batch_size=32,
		shuffle=False,
		drop_last=False,
	)

	############################################################################################################################
	# Testing
	#

	model.eval()

	# Apply model
	pred_label_list = []
	num_step = len(test_loader)
	pbar = tqdm.trange(num_step, desc='Testing')

	for step, inputs_cpu in zip(pbar, test_loader):
		inputs = tuple(v.cuda() for v in inputs_cpu)
		pred_label_list.append(model.predict(*inputs))

	# Concatenate result
	pred_nid = model.label_encoder.inverse_transform(np.concatenate(pred_label_list))
	true_gid = model.label_encoder.inverse_transform(test_data.label.cpu().data.numpy())

	# Check accuracy
	from sklearn.metrics import accuracy_score, f1_score
	print()

	acc = accuracy_score(true_gid, pred_nid)
	print(f'Overall Accuracy = {acc*100:05.2f}%')

	f1 = f1_score(true_gid, pred_nid, average='weighted')
	print(f'Overall F1 Score = {f1*100:05.2f}%')

	if 'PID' in true_gid or 'PID' in pred_nid:
		f1_pid, = f1_score(true_gid, pred_nid, average=None, labels=['PID'])
		print(f'PID     F1 Score = {f1_pid*100:05.2f}%')

	if 'OSP' in true_gid or 'OSP' in pred_nid:
		f1_osp, = f1_score(true_gid, pred_nid, average=None, labels=['OSP'])
		print(f'OSP     F1 Score = {f1_osp*100:05.2f}%')

	if 'GP'  in true_gid or 'GP'  in pred_nid:
		f1_gp, = f1_score(true_gid, pred_nid, average=None, labels=['GP'])
		print(f'GP      F1 Score = {f1_gp*100:05.2f}%')

	pass
