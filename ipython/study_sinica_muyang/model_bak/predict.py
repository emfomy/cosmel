#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import os
import sys

import numpy as np

import torch

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
	print(f'model      = {args.model}')
	print(f'data_file  = {data_file}')
	print(f'model_file = {model_file}')
	print(f'meta_file  = {meta_file}')
	print(f'data_type  = {data_type}')
	print()
	print(f'xargs      = {xargs}')
	print()

	if args.check: exit()

	# Load model
	meta  = DataSetMeta.load(meta_file)
	model = Model(meta, xargs)
	model.cuda()
	print()
	model.load(model_file)
	print(f'Loaded model from "{model_file}"')
	print()
	model.eval()

	# Load dataset
	asmid_list = AsmidList.load(data_file)
	if data_type == 'sp':
		asmid_list.filter_sp()
	if data_type == 'mtype':
		asmid_list.gid_to_mtype()
	print()
	dataset = model.dataset_predict(asmid_list)

	# Set batch size
	num_test = len(dataset)
	num_step = max(num_test // 500, 1)
	print(f'num_test = {num_test}')

	# Apply model
	pred_batch_gid = []
	for step, batch in enumerate(dataset.batch(num_step, shuffle=False, drop_last=False)):
		inputs = model.inputs_predict(batch).cuda()
		pred_batch_gid.append(model.predict(inputs))
		printr(f'Batch: {step+1:0{len(str(num_step))}}/{num_step}')

	print()

	# Concatenate result
	pred_gid = np.concatenate(pred_batch_gid)
	raw_data = dataset.raw(None)
	true_gid = raw_data.gid

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
