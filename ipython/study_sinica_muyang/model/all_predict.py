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
from predict import check_accuracy


if __name__ == '__main__':

	# Parse arguments
	argparser = argparse.ArgumentParser(description='Test StyleMe model.')

	arggroup = argparser.add_mutually_exclusive_group()
	arggroup.add_argument('-v', '--ver', metavar='<ver>#<date>', \
			help='set <dir> as "result/<ver>_<date>"')
	arggroup.add_argument('-D', '--dir', metavar='<dir>', \
			help='prepend <dir> to data and model path')

	argparser.add_argument('-d', '--data', metavar='<data_name>', required=True, \
			help='testing data path; load data from "[<dir>]<data_name>.list.txt"')
	argparser.add_argument('-w', '--weight', metavar='<weight_name>', required=True, \
			help='model weight path; load model weight from "[<dir>]<weight_name>.<model_type>.weight.pt"')
	argparser.add_argument('-m', '--model', metavar='<model_type>', required=True, \
		  help='use model <model_type>')
	argparser.add_argument('-w0', '--weight0', metavar='<weight0_name>', \
		  help='use model <weight0_name>; default is "<weight_name>"')
	argparser.add_argument('-m0', '--model0', metavar='<model0_type>', default='model0', \
		  help='use model <model0_type>; default is "model0"')
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
	weight0 = args.weight
	if args.weight0 != None:
		weight0 = args.weight0
	model0_file   = f'{result_root}{weight0}.{args.model0}.pt'

	meta_file     = f'{result_root}meta.pkl'
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
	print(f'model         = {args.model}')
	print(f'data_file     = {data_file}')
	print(f'model_file    = {model_file}')
	print(f'model0_file   = {model0_file}')
	print(f'meta_file     = {meta_file}')
	print()

	if args.check: exit()

	############################################################################################################################
	# Load data
	#

	meta        = DataSetMeta.load(meta_file)
	asmid_list  = AsmidList.load(data_file)
	asmid_list0 = AsmidList(asmid_list)

	############################################################################################################################
	# Create model
	#

	model = Model(meta)
	model.cuda()
	print()
	print(model)
	print()
	model.load(model_file)
	print(f'Loaded model from "{model_file}"')
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
	model0.load(model0_file)
	print(f'Loaded model0 from "{model0_file}"')
	print()
	model0.eval()

	############################################################################################################################
	# DataSet
	#

	data    = model.data_predict_all(asmid_list)
	dataset = torch.utils.data.TensorDataset(*data)
	print(f'nun_test = {len(dataset)}')
	loader  = torch.utils.data.DataLoader(
		dataset=dataset,
		batch_size=32,
		shuffle=False,
		drop_last=False,
	)

	############################################################################################################################
	# DataSet of Model0
	#

	data0    = model0.data_predict_all(asmid_list0)
	dataset0 = torch.utils.data.TensorDataset(*data0)
	print(f'nun_test = {len(dataset0)}')
	loader0  = torch.utils.data.DataLoader(
		dataset=dataset0,
		batch_size=32,
		shuffle=False,
		drop_last=False,
	)

	############################################################################################################################
	# Predicting
	#

	# Apply model
	pred_label_list = []
	true_label_list = []
	num_step = len(loader)

	pbar = tqdm.trange(num_step)
	for step, inputs in zip(pbar, loader):
		inputs_gpu = tuple(v.cuda() for v in inputs)
		output = model(*inputs_gpu[:-1])
		pred_label_list.append(model.predict(output))
		true_label_list.append(inputs_gpu[-1].cpu().data.numpy())

	# Concatenate result
	pred_gid = model.label_encoder.inverse_transform(np.concatenate(pred_label_list))
	true_gid = model.label_encoder.inverse_transform(np.concatenate(true_label_list))

	############################################################################################################################
	# Predicting Model0
	#

	# Apply model
	pred_label0_list = []
	true_label0_list = []
	num_step0 = len(loader0)

	pbar0 = tqdm.trange(num_step0)
	for step, inputs0 in zip(pbar0, loader0):
		inputs0_gpu = tuple(v.cuda() for v in inputs0)
		output0 = model0(*inputs0_gpu[:-1])
		pred_label0_list.append(model0.predict(output0))
		true_label0_list.append(inputs0_gpu[-1].cpu().data.numpy())

	# Concatenate result
	pred_gid0 = model0.label_encoder.inverse_transform(np.concatenate(pred_label0_list))
	true_gid0 = model0.label_encoder.inverse_transform(np.concatenate(true_label0_list))

	############################################################################################################################
	# Merge result
	#

	pred_idx0 = (pred_gid0 != 'PID')
	pred_gid[pred_idx0] = pred_gid0[pred_idx0]

	true_idx0 = (true_gid0 != 'PID')
	true_gid[true_idx0] = true_gid0[true_idx0]

	############################################################################################################################
	# Check accuracy
	#
	check_accuracy(true_gid, pred_gid)

	pass
