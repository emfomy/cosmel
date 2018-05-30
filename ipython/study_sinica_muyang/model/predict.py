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

from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from styleme import *
from model.module.meta import *

def check_accuracy(true_gid, pred_gid):

	# from sklearn.metrics import classification_report
	# print(classification_report(true_gid, pred_gid))
	# return

	# from sklearn.metrics import accuracy_score, f1_score
	# print(f'accuracy = {accuracy_score(true_gid, pred_gid)}')
	# print(f'F1 score = {f1_score(true_gid, pred_gid, average="weighted")}')
	# print(f'F1 (PID) = {f1_score(true_gid, pred_gid, average=None, labels=["PID"])[0]}')
	# print(f'F1 (OSP) = {f1_score(true_gid, pred_gid, average=None, labels=["OSP"])[0]}')
	# print(f'F1 (GP)  = {f1_score(true_gid, pred_gid, average=None, labels=["GP"])[0]}')
	# return

	def model_accuracy(true_gid, pred_gid, mask=slice(None,None), name='accuracy'):
		assert (np.shape(true_gid) == np.shape(pred_gid))
		correct = (true_gid[mask] == pred_gid[mask])
		csum = correct.sum()
		clen = correct.size
		accuracy = csum / clen
		print(f'{name} = {accuracy} ({csum}/{clen})')

	model_accuracy(true_gid, pred_gid, slice(None,None),                'accuracy       ')

	if 'PID' not in true_gid and 'PID' not in pred_gid:
		model_accuracy(true_gid, pred_gid, [i.isdigit() for i in pred_gid], 'precision (ID) ')
		model_accuracy(true_gid, pred_gid, [i.isdigit() for i in true_gid], 'recall    (ID) ')

	if 'PID' in true_gid or 'PID' in pred_gid:
		model_accuracy(true_gid, pred_gid, pred_gid == 'PID',               'precision (PID)')
		model_accuracy(true_gid, pred_gid, true_gid == 'PID',               'recall    (PID)')

	if 'OSP' in true_gid or 'OSP' in pred_gid:
		model_accuracy(true_gid, pred_gid, pred_gid == 'OSP',               'precision (OSP)')
		model_accuracy(true_gid, pred_gid, true_gid == 'OSP',               'recall    (OSP)')

	if 'GP' in true_gid or 'GP' in pred_gid:
		model_accuracy(true_gid, pred_gid, pred_gid == 'GP',                'precision (GP) ')
		model_accuracy(true_gid, pred_gid, true_gid == 'GP',                'recall    (GP) ')

	from sklearn.metrics import confusion_matrix
	print(confusion_matrix(true_gid, pred_gid))


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
	argparser.add_argument('-t', '--num-tests', metavar='<num>', type=int,
			help='number of tests.')
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

	num_test = args.num_tests

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
	print(f'num_test      = {num_test}')
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
	model.eval()

	############################################################################################################################
	# DataSet
	#

	data    = model.ment_data(asmid_list)
	dataset = torch.utils.data.TensorDataset(*data.inputs)
	print(f'nun_test = {len(dataset)}')
	loader  = torch.utils.data.DataLoader(
		dataset=dataset,
		batch_size=32,
		shuffle=False,
		drop_last=False,
	)

	############################################################################################################################
	# Predicting
	#

	total_test = num_test if num_test else 1
	acc        = np.zeros((total_test, 5,))

	for t in range(max(total_test, 1)):

		if num_test:
			model_file = f'{result_root}{args.weight}.{t}.{args.model}.pt'

		# Load model
		model.load(model_file)
		# print(f'Loaded model from "{model_file}"')

		# Apply model
		pred_label_list = []
		num_step = len(loader)
		pbar = tqdm.trange(num_step, desc=f'Test {t+1:0{len(str(total_test))}}/{total_test}')

		for step, inputs_cpu in zip(pbar, loader):
			inputs = tuple(v.cuda() for v in inputs_cpu)
			pred_label_list.append(model.predict(*inputs))

		# Concatenate result
		pred_gid = model.label_encoder.inverse_transform(np.concatenate(pred_label_list))
		true_gid = model.label_encoder.inverse_transform(data.label.cpu().data.numpy())

		# Check accuracy
		from sklearn.metrics import accuracy_score, f1_score
		acc[t, 0]  = accuracy_score(true_gid, pred_gid)
		acc[t, 1]  = f1_score(true_gid, pred_gid, average='weighted')
		acc[t, 2:] = f1_score(true_gid, pred_gid, average=None, labels=['PID', 'OSP', 'GP'])

	acc = acc*100

	np.set_printoptions(formatter={'float_kind': (lambda x: f'{x:05.2f}')})
	print()
	print('  acc   f1    PID   OSP   GP')
	print(acc)
	print()
	print('mean')
	print(np.mean(acc, axis=0))
	print('std')
	print(np.std(acc, axis=0))

	pass
