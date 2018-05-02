#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import itertools
import os
import sys

import numpy as np

import torch
import torch.utils.data

sys.path.insert(0, os.path.abspath('.'))
from styleme import *
from meta import *

def model_accuracy(pred_gid_code, true_gid_code, mask=slice(None,None), name='accuracy'):
	assert (np.shape(pred_gid_code) == np.shape(true_gid_code))
	correct = (pred_gid_code[mask] == true_gid_code[mask])
	csum = correct.sum()
	clen = correct.size
	accuracy = csum / clen
	print(f'{name} = {accuracy} ({csum}/{clen})')


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
	print(f'meta_file     = {meta_file}')
	print()

	if args.check: exit()

	############################################################################################################################
	# Load data
	#

	meta       = DataSetMeta.load(meta_file)
	asmid_list = AsmidList.load(data_file)

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
	# DataSet
	#

	inputs  = model.data_predict(asmid_list)
	dataset = torch.utils.data.TensorDataset(*inputs)
	print(f'nun_test = {len(dataset)}')
	loader  = torch.utils.data.DataLoader(
		dataset=dataset,
		batch_size=32,
		shuffle=False,
		drop_last=False,
	)

	############################################################################################################################
	# Training
	#

	# Apply model
	pred_label_list = []
	true_label_list = []
	num_step = len(loader)

	for step, inputs in enumerate(loader):
		inputs_gpu = tuple(v.cuda() for v in inputs)
		output = model(*inputs_gpu[:-1])
		pred_label_list.append(model.predict(output))
		true_label_list.append(inputs[-1].cpu().data.numpy())
		printr(f'Batch: {step+1:0{len(str(num_step))}}/{num_step}')

	print()

	# Concatenate result
	pred_gid = model.label_encoder.inverse_transform(np.concatenate(pred_label_list))
	true_gid = model.label_encoder.inverse_transform(np.concatenate(true_label_list))

	# Check accuracy
	model_accuracy(pred_gid, true_gid, slice(None,None),                'accuracy       ')

	model_accuracy(pred_gid, true_gid, [i.isdigit() for i in pred_gid], 'precision (ID) ')
	model_accuracy(pred_gid, true_gid, [i.isdigit() for i in true_gid], 'recall    (ID) ')

	model_accuracy(pred_gid, true_gid, pred_gid == 'PID',               'precision (PID)')
	model_accuracy(pred_gid, true_gid, true_gid == 'PID',               'recall    (PID)')

	model_accuracy(pred_gid, true_gid, pred_gid == 'OSP',               'precision (OSP)')
	model_accuracy(pred_gid, true_gid, true_gid == 'OSP',               'recall    (OSP)')

	model_accuracy(pred_gid, true_gid, pred_gid == 'GP',                'precision (GP) ')
	model_accuracy(pred_gid, true_gid, true_gid == 'GP',                'recall    (GP) ')

	from sklearn.metrics import confusion_matrix
	print(confusion_matrix(true_gid, pred_gid))

	pass
