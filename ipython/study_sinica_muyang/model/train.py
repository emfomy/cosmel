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
			help='use model <model_type>')
	argparser.add_argument('-t', '--data-type', metavar='<data_type>', \
			choices=['sp', 'mtype'], help='process data type preprocessing')
	argparser.add_argument('--meta', metavar='<meta_name>', \
			help='dataset meta path; default is "[<dir>/]meta.pkl"')

	argparser.add_argument('--xargs', help='Extra arguments for the model')

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

	data_type = args.data_type

	xargs = []
	if args.xargs != None:
		xargs = args.xargs.split()

	# Print arguments
	print()
	print(args)
	print()
	print(f'model         = {args.model}')
	print(f'data_file     = {data_file}')
	print(f'model_file    = {model_file}')
	print(f'pretrain_file = {pretrain_file}')
	print(f'meta_file     = {meta_file}')
	print(f'data_type     = {data_type}')
	print()
	print(f'xargs         = {xargs}')
	print()

	if args.check: exit()

	# Create model
	meta  = DataSetMeta.load(meta_file)
	model = Model(meta, xargs)
	model.cuda()
	print()
	print(model)
	print()

	# Load dataset
	asmid_list = AsmidList.load(data_file)
	if data_type == 'sp':
		asmid_list.filter_sp()
	if data_type == 'mtype':
		asmid_list.gid_to_mtype()
	print()
	dataset = model.dataset(asmid_list)

	# Set batch size
	num_train = len(dataset)
	num_step  = max(num_train // 500, 1)
	print(f'num_train = {num_train}')

	# Create optimizer
	optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()))

	# Train
	num_epoch = 20
	for epoch in range(num_epoch):

		for step, batch in enumerate(dataset.batch(num_step)):

			# Forward and compute loss
			inputs = model.inputs(batch).cuda()
			losses = model(inputs)
			loss = sum(losses.values())
			printr( \
					f'Epoch: {epoch+1:0{len(str(num_epoch))}}/{num_epoch}' + \
					f' | Batch: {step+1:0{len(str(num_step))}}/{num_step}' + \
					f' | loss: {loss.data.item():.6f}' + \
					''.join([f' | {k}: {v.data.item():.6f}' for k, v in losses.items()]))
			sys.stdout.flush()

			optimizer.zero_grad()
			loss.backward()
			optimizer.step()

		print()

	# Save models
	model.save(model_file)
	print(f'Saved training model into "{model_file}"')

	pass
