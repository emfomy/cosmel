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
from data import *
from train import Inputs

def model_accuracy(predict_gid_code, true_gid_code, mask=slice(None,None), name='all'):
	assert (np.shape(predict_gid_code) == np.shape(true_gid_code))
	correct = (predict_gid_code[mask] == true_gid_code[mask])
	accuracy = correct.sum() / correct.size
	print(f'accuracy ({name}) = {accuracy} ({correct.sum()}/{correct.size})')

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
			help='model weight path; load model weight from "[<dir>]<weight_name>.weight.pt"')
	argparser.add_argument('-m', '--model', metavar='<model_name>', choices=['model2', 'model3'], required=True, \
			help='use model from <model_name>')
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
	model_file    = f'{result_root}{args.weight}.weight.pt'

	if args.model == 'model2':
		from model2 import Model2 as Model
	elif args.model == 'model3':
		from model3 import Model3 as Model

	meta_file     = f'{result_root}meta.pkl'
	if args.meta != None:
		meta_file = args.meta

	# Print arguments
	print()
	print(args)
	print()
	print(f'data_file  = {data_file}')
	print(f'model_file = {model_file}')
	print(f'meta_file  = {meta_file}')
	print()

	if args.check: exit()

	# Load data
	meta         = DatasetMeta.load(meta_file)
	asmid_list   = AsmidList.load(data_file)
	text_dataset = MentionDataset(meta, asmid_list)
	num_test     = len(text_dataset)
	print(f'num_test      = {num_test}')

	# Set batch size
	num_text        = len(text_dataset)
	text_batch_size = 500
	num_step        = int(np.ceil(num_text/text_batch_size))

	# Load model
	model = Model(meta)
	model.cuda()
	print()
	model.load(model_file)
	print(f'Loaded model from "{model_file}"')
	print()

	# Apply model
	predict_batch_prob = [None] * num_step
	text_batch_idxs = np.split(range(num_text), range(text_batch_size, num_text, text_batch_size))
	for step, text_batch_idx in zip(range(num_step), text_batch_idxs):
		text_batch = text_dataset[text_batch_idx]
		inputs = Inputs(**text_batch)
		inputs.cuda()
		predict_batch_prob[step] = model.predict(**vars(inputs)).cpu().data.numpy()
		printr(f'Batch: {step+1:0{len(str(num_step))}}/{num_step}')

	print()

	# Concatenate result
	predict_prob = np.concatenate(predict_batch_prob)
	predict_gid_code = np.argmax(predict_prob, axis=1)
	text_gid_code = text_dataset[:]['gid_code'].numpy()

	# Check accuracy
	osp_code = meta.p_encoder.transform(['OSP'])[0]
	gp_code  = meta.p_encoder.transform(['GP'])[0]
	model_accuracy(predict_gid_code, text_gid_code)
	model_accuracy(predict_gid_code, text_gid_code, text_gid_code == osp_code, 'OSP')
	model_accuracy(predict_gid_code, text_gid_code, text_gid_code == gp_code,  'GP')

	pass
