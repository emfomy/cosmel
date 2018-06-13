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


	argparser.add_argument('-c', '--corpus', required=True,
		help='store corpus data in directory "<CORPUS>/"')
	argparser.add_argument('-m', '--model', required=True,
		help='store model data in directory "<MODEL>/"')

	argparser.add_argument('-i', '--input', default='purged_article_grid', \
			help='load mention from "<CORPUS>/mention/<IN-DIR>/"; default is "purged_article_grid"')
	argparser.add_argument('-l', '--label', choices=['gid', 'nid', 'rid'], required=True, \
			help='training label type')
	argparser.add_argument('-s', '--structure', required=True, \
			help='model structure')

	argparser.add_argument('-w', '--weight', \
			help='output weight name; output model weight into "<MODEL>/<WEIGHT>.<STRUCTURE>.weight.pt"; ' + \
					'default "[<PRETRAIN>+]<LABEL>"')
	argparser.add_argument('-p', '--pretrain', \
			help='pretrained weight name; load model weight from "<MODEL>/<PRETRAIN>.<STRUCTURE>.weight.pt"')

	argparser.add_argument('--epoch', type=int, default=10, \
			help='train <EPOCH> times; default is 10')
	argparser.add_argument('--test_size', type=float, default=0.3, \
			help='split <TEST-SIZE> mentions for testing; default is 0.3')

	argparser.add_argument('-k', '--check', action='store_true', help='Check arguments')

	args = argparser.parse_args()

	corpus_root = os.path.normpath(args.corpus)
	model_root  = os.path.normpath(args.model)

	in_dir      = args.input

	target       = f'purged_article'
	article_root = f'{corpus_root}/article/{target}_role'
	mention_root = f'{corpus_root}/mention/{in_dir}'
	bad_article  = f'{corpus_root}/article/bad_article.txt'

	label_type = args.label

	if args.weight != None:
		weight_name = args.weight
	elif args.pretrain != None:
		weight_name = f'{args.pretrain}+{label_type}'
	else:
		weight_name = f'{label_type}'
	model_file = f'{model_root}/{weight_name}.{args.structure}.pt'

	pretrain_file = ''
	if args.pretrain != None:
		pretrain_file = f'{model_root}/{args.pretrain}.{args.structure}.pt'

	meta_file = f'{model_root}/meta.pkl'

	num_epoch = args.epoch
	test_size = args.test_size

	model_pkg_name = args.structure
	model_cls_name = args.structure.capitalize()
	Model = getattr(__import__('module.'+model_pkg_name, fromlist=model_cls_name), model_cls_name)

	# Print arguments
	print()
	print(args)
	print()
	print(f'article_root  = {article_root}')
	print(f'mention_root  = {mention_root}')
	print(f'bad_article   = {bad_article}')
	print()
	print(f'model         = {model_cls_name}')
	print(f'model_file    = {model_file}')
	print(f'pretrain_file = {pretrain_file}')
	print(f'meta_file     = {meta_file}')
	print(f'num_epoch     = {num_epoch}')
	print(f'test_size     = {test_size}')
	print()

	if args.check: sys.exit()

	############################################################################################################################
	# Initialize model
	#

	# Load data
	corpus = Corpus(article_root, mention_root=mention_root, skip_file=bad_article)

	for m in corpus.mention_set:
		if m.gid == 'NAP': m.set_gid('GP')
		if m.nid == 'NAP': m.set_nid('GP')
		if m.rid == 'NAP': m.set_rid('GP')
		m.set_gid(getattr(m, label_type))

	ment_list = MentionList(corpus, [m for m in corpus.mention_set if m.gid])
	meta      = DataSetMeta.load(meta_file)
	print()

	# Split training and testing data
	train_ment_list, test_ment_list = ment_list.train_test_split(test_size=test_size, random_state=0, shuffle=True)

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
	ment_data    = model.ment_data(train_ment_list)
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
	test_data    = model.ment_data(test_ment_list)
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
