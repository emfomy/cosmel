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

	argparser.add_argument('-v', '--ver', metavar='<ver>#<cver>#<mver>', required=True, \
		help='load repo from "data/<ver>/", load corpus data from "data/<ver>/corpus/<cver>/", ' + \
				'and load/save model data from/into "data/<ver>/model/<mver>/"; the default value of <mver> is <cver>')

	argparser.add_argument('-i', '--input', metavar='<in_dir>', default='purged_article_gid', \
			help='load mention from "data/<ver>/corpus/<cver>/mention/<in_dir>"; default is "purged_article_gid"')
	argparser.add_argument('-o', '--output', metavar='<out_dir>', default='purged_article_nid', \
			help='svae mention into "data/<ver>/corpus/<cver>/mention/<out_dir>"; default is "purged_article_nid"')

	argparser.add_argument('-w', '--weight', metavar='<weight_name>', required=True, \
			help='load model weight "data/<ver>/model/<mver>/<weight_name>.<model_type>.weight.pt"')
	argparser.add_argument('-m', '--model', metavar='<model_type>', required=True, \
			help='use model <model_type>')

	argparser.add_argument('-w0', '--weight0', metavar='<weight0_name>', \
			help='load model weight "data/<ver>/model/<mver>/<weight_0name>.<model0_type>.weight.pt"')
	argparser.add_argument('-m0', '--model0', metavar='<model0_type>', default='model0', \
		  help='use model <model0_type>; default is "model0"')

	argparser.add_argument('--meta', metavar='<meta_name>', \
			help='dataset meta path; default is "data/<ver>/model/<mver>/meta.pkl"')

	argparser.add_argument('-c', '--check', action='store_true', help='Check arguments')

	args = argparser.parse_args()

	vers = args.ver.split('#')
	assert 2 <= len(vers) <= 3, argparser.format_usage()
	ver  = vers[0]
	cver = vers[1]
	mver = vers[-1]
	assert len(ver)  > 0
	assert len(cver) > 0
	assert len(mver) > 0

	data_root   = f'data/{ver}'
	corpus_root = f'data/{ver}/corpus/{cver}'
	model_root  = f'data/{ver}/model/{mver}'

	in_dir  = args.input
	out_dir = args.output

	target       = f'purged_article'
	article_root = f'{corpus_root}/article/{target}_role'
	input_root   = f'{corpus_root}/mention/{in_dir}'
	output_root  = f'{corpus_root}/mention/{out_dir}'
	bad_article  = f'{corpus_root}/article/bad_article.txt'

	model_file  = f'{model_root}/{args.weight}.{args.model}.pt'

	weight0_name = args.weight
	if args.weight0 != None:
		weight0_name = args.weight0
	model0_file = f'{model_root}/{weight0_name}.{args.model0}.pt'

	meta_file = f'{model_root}/meta.pkl'
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
	print(f'article_root = {article_root}')
	print(f'input_root   = {input_root}')
	print(f'output_root  = {output_root}')
	print(f'bad_article  = {bad_article}')
	print()
	print(f'model         = {model_cls_name}')
	print(f'model0        = {model0_cls_name}')
	print(f'model_file    = {model_file}')
	print(f'model0_file   = {model0_file}')
	print(f'meta_file     = {meta_file}')
	print()

	if args.check: sys.exit()

	############################################################################################################################
	# Load data
	#

	corpus     = Corpus(article_root, mention_root=input_root, skip_file=bad_article)
	corpus0    = Corpus(article_root, mention_root=input_root, skip_file=bad_article)
	ment_list  = MentionList(corpus, [m for m in corpus.mention_set  if not m.nid])
	ment0_list = MentionList(corpus, [m for m in corpus0.mention_set if not m.nid])
	meta      = DataSetMeta.load(meta_file)
	print()

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

	data    = model.ment_data_all(ment_list)
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

	data0    = model0.ment_data_all(ment0_list)
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

	del corpus
	del corpus0

	corpus    = Corpus(article_root, mention_root=input_root, skip_file=bad_article)
	ment_list = MentionList(corpus, [m for m in corpus.mention_set  if not m.nid])
	for m, nid in zip(ment_list, pred_nid):
		m.set_nid(nid)

	n = str(len(corpus.mention_bundle_set))
	for i, bundle in enumerate(corpus.mention_bundle_set):
		output_file = transform_path(bundle.path, input_root, output_root, '.json')
		printr(f'{i+1:0{len(n)}}/{n}\t{output_file}')
		bundle.save(output_file)
	print()

	pass
