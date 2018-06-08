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

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *
from model.module.meta import *


if __name__ == '__main__':

	# Parse arguments
	argparser = argparse.ArgumentParser(description='Apply CosmEL model.')

	arggroup = argparser.add_mutually_exclusive_group()
	arggroup.add_argument('-v', '--ver', metavar='<ver>#<date>', \
			help='set <dir> as "data/<ver>/model/<date>"')
	arggroup.add_argument('-D', '--dir', metavar='<dir>', \
			help='prepend <dir> to data and model path')

	argparser.add_argument('-d', '--data', metavar='<data_name>', required=True, \
			help='input data path; load data from "[<dir>/]<data_name>.list.txt"')
	argparser.add_argument('-w', '--weight', metavar='<weight_name>', required=True, \
			help='model weight path; load model weight from "[<dir>/]<weight_name>.<model_type>.weight.pt"')
	argparser.add_argument('-m', '--model', metavar='<model_type>', required=True, \
		  help='use model <model_type>')
	argparser.add_argument('-w0', '--weight0', metavar='<weight0_name>', \
		  help='use model <weight0_name>; default is "<weight_name>"')
	argparser.add_argument('-m0', '--model0', metavar='<model0_type>', default='model0', \
		  help='use model <model0_type>; default is "model0"')
	argparser.add_argument('--meta', metavar='<meta_name>', \
			help='dataset meta path; default is "[<dir>/]meta.pkl"')
	argparser.add_argument('-o', '--output', metavar='<out_dir>', required=True, \
			help='output data path; load data from "[<dir>/]<out_dir>"')

	argparser.add_argument('-c', '--check', action='store_true', help='Check arguments')

	args = argparser.parse_args()

	vers = args.ver.split('#')
	assert len(vers) == 2, argparser.format_usage()
	ver  = vers[0]
	date = vers[1]

	data_root = f'data/{ver}'
	tmp_root  = f'data/tmp'

	result_root = ''
	if args.ver != None:
		result_root = f'{data_root}/model/{date}'
	if args.dir != None:
		result_root = f'{args.dir}'

	data_file   = f'{result_root}/{args.data}.list.txt'
	model_file  = f'{result_root}/{args.weight}.{args.model}.pt'
	weight0 = args.weight
	if args.weight0 != None:
		weight0 = args.weight0
	model0_file = f'{result_root}/{weight0}.{args.model0}.pt'

	output_file = f'{result_root}/output/{args.output}.list.txt'

	meta_file   = f'{result_root}/meta.pkl'
	if args.meta != None:
		meta_file = args.meta

	model_pkg_name = args.model
	model_cls_name = args.model.capitalize()
	Model = getattr(__import__('module.'+model_pkg_name, fromlist=model_cls_name), model_cls_name)

	model0_pkg_name = args.model0
	model0_cls_name = args.model0.capitalize()
	Model0 = getattr(__import__('module.'+model0_pkg_name, fromlist=model0_cls_name), model0_cls_name)

	# Print arguments
	print()
	print(args)
	print()
	print(f'model       = {args.model}')
	print(f'data_file   = {data_file}')
	print(f'model_file  = {model_file}')
	print(f'model0_file = {model0_file}')
	print(f'meta_file   = {meta_file}')
	print(f'output_file = {output_file}')
	print()

	if args.check: exit()

	############################################################################################################################
	# Load data
	#

	meta        = DataSetMeta.load(meta_file)
	asmid_list  = AsmidList.load(data_file)
	asmid_list0 = asmid_list.copy()

	############################################################################################################################
	# Create model
	#

	model = Model(meta)
	model.cuda()
	print()
	print(model)
	print()
	model.eval()

	############################################################################################################################
	# Create model of Model0
	#

	model0 = Model0(meta)
	model0.cuda()
	print()
	print(model0)
	print()
	model0.eval()

	############################################################################################################################
	# DataSet
	#

	data    = model.ment_data_all(asmid_list)
	dataset = torch.utils.data.TensorDataset(*data.inputs)
	print(f'#mention = {len(dataset)}')
	loader  = torch.utils.data.DataLoader(
		dataset=dataset,
		batch_size=32,
		shuffle=False,
		drop_last=False,
	)

	############################################################################################################################
	# DataSet of Model0
	#

	data0    = model0.ment_data_all(asmid_list0)
	dataset0 = torch.utils.data.TensorDataset(*data0.inputs)
	print(f'#mention = {len(dataset0)}')
	loader0  = torch.utils.data.DataLoader(
		dataset=dataset0,
		batch_size=32,
		shuffle=False,
		drop_last=False,
	)

	############################################################################################################################
	# Predicting
	#

	# Load model
	model.load(model_file)
	print(f'Loaded model from "{model_file}"')
	model0.load(model0_file)
	print(f'Loaded model0 from "{model0_file}"')

	# Apply model
	pred_label_list = []
	num_step = len(loader)

	pbar = tqdm.trange(num_step, desc=model_cls_name)
	for step, inputs_cpu in zip(pbar, loader):
		inputs = tuple(v.cuda() for v in inputs_cpu)
		pred_label_list.append(model.predict(*inputs))

	# Concatenate result
	pred_nid = model.label_encoder.inverse_transform(np.concatenate(pred_label_list))

	# Apply model0
	pred_label0_list = []
	num_step0 = len(loader0)

	pbar0 = tqdm.trange(num_step0, desc=model0_cls_name)
	for step, inputs0_cpu in zip(pbar0, loader0):
		inputs0 = tuple(v.cuda() for v in inputs0_cpu)
		pred_label0_list.append(model0.predict(*inputs0))

	# Concatenate result0
	pred_nid0 = model0.label_encoder.inverse_transform(np.concatenate(pred_label0_list))

	# Merge result
	pred_idx0 = (pred_nid0 != 'PID')
	pred_nid[pred_idx0] = pred_nid0[pred_idx0]

	############################################################################################################################
	# Writing Results
	#

	asmid_list_output = AsmidList.load(data_file)
	for asmid, nid in zip(asmid_list_output, pred_nid):
		asmid.nid = nid
	asmid_list_output.dump(output_file)

	pass
