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
	accuracy = correct.sum() / correct.size
	print(f'{name} = {accuracy} ({correct.sum()}/{correct.size})')

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

	if   args.model == 'model2c':
		from module.model2c   import Model2c   as Model
	elif args.model == 'model2cd':
		from module.model2cd  import Model2cd  as Model
	elif args.model == 'model2cn':
		from module.model2cn  import Model2cp  as Model
	elif args.model == 'model2cdn':
		from module.model2cdn import Model2cdp as Model

	meta_file     = f'{result_root}meta.pkl'
	if args.meta != None:
		meta_file = args.meta

	# Print arguments
	print()
	print(args)
	print()
	print(f'model      = {args.model}')
	print(f'data_file  = {data_file}')
	print(f'model_file = {model_file}')
	print(f'meta_file  = {meta_file}')
	print()

	if args.check: exit()

	# Load model
	meta  = DatasetMeta.load(meta_file)
	model = Model(meta)
	model.cuda()
	print()
	model.load(model_file)
	print(f'Loaded model from "{model_file}"')
	print()

	# Load dataset
	asmid_list = AsmidList.load(data_file)
	dataset    = model.dataset(asmid_list)

	# Set batch size
	num_test = len(dataset)
	num_step = num_test // 500
	print(f'num_test      = {num_test}')

	# Apply model
	pred_batch_prob = [None] * num_step
	for step, inputs in enumerate(dataset.batch(num_step)):
		inputs.cuda()
		pred_batch_prob[step] = model.predict(inputs).cpu().data.numpy()
		printr(f'Batch: {step+1:0{len(str(num_step))}}/{num_step}')

	print()

	# Concatenate result
	pred_prob = np.concatenate(pred_batch_prob)
	pred_gid = meta.p_encoder.inverse_transform(np.argmax(pred_prob, axis=1))
	raw_data = dataset.raw(None)
	true_gid = raw_data.gid

	# Check accuracy
	model_accuracy(pred_gid, true_gid, slice(None,None),                'accuracy       ')

	model_accuracy(pred_gid, true_gid, [i.isdigit() for i in pred_gid], 'precision (PID)')
	model_accuracy(pred_gid, true_gid, [i.isdigit() for i in true_gid], 'recall    (PID)')

	model_accuracy(pred_gid, true_gid, pred_gid == 'OSP',               'precision (OSP)')
	model_accuracy(pred_gid, true_gid, true_gid == 'OSP',               'recall    (OSP)')

	model_accuracy(pred_gid, true_gid, pred_gid == 'GP',                'precision (GP) ')
	model_accuracy(pred_gid, true_gid, true_gid == 'GP',                'recall    (GP) ')

	pass
