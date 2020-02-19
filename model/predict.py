#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <http://muyang.pro>'
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

	argparser.add_argument('-c', '--corpus', required=True,
			help='store corpus data in directory "<CORPUS>/"')
	argparser.add_argument('-m', '--model', required=True,
			help='store model data in directory "<MODEL>/"; default is "<CORPUS>/model/"')

	argparser.add_argument('-i', '--input', default='purged_article_rid', \
			help='load mention from "<CORPUS>/mention/<INPUT>/"; default is "purged_article_rid"')
	argparser.add_argument('-o', '--output', default='purged_article_nrid', \
			help='save mention into "<CORPUS>/mention/<OUTPUT>/"; default is "purged_article_nrid"')

	argparser.add_argument('-s', '--structure-eem', \
			help='use model structure <STRUCTURE-EEM> for entity embeddings model')
	argparser.add_argument('-S', '--structure-mtc', \
			help='use model structure <STRUCTURE-MTC> for mention type classifier')
	argparser.add_argument('-l', '--label-eem', \
			help='use label type <LABEL-EEM> for entity embeddings model')
	argparser.add_argument('-L', '--label-mtc', \
			help='use label type <LABEL-MTC> for mention type classifier')

	argparser.add_argument('-k', '--check', action='store_true', help='Check arguments')

	args = argparser.parse_args()

	corpus_root = os.path.normpath(args.corpus)
	model_root  = os.path.normpath(args.model)

	in_dir  = args.input
	out_dir = args.output

	target       = f'purged_article'
	article_root = f'{corpus_root}/article/{target}_role'
	input_root   = f'{corpus_root}/mention/{in_dir}'
	output_root  = f'{corpus_root}/mention/{out_dir}'
	bad_article  = f'{corpus_root}/article/bad_article.txt'

	model0_file = f'{model_root}/{args.label_mtc}.{args.structure_mtc}.pt'
	model1_file = f'{model_root}/{args.label_eem}.{args.structure_eem}.pt'

	meta_file = f'{model_root}/meta.pkl'

	model0_pkg_name = args.structure_mtc
	model0_cls_name = args.structure_mtc.capitalize()
	Model0 = getattr(__import__('module.'+model0_pkg_name, fromlist=model0_cls_name), model0_cls_name)

	model1_pkg_name = args.structure_eem
	model1_cls_name = args.structure_eem.capitalize()
	Model1 = getattr(__import__('module.'+model1_pkg_name, fromlist=model1_cls_name), model1_cls_name)

	# Print arguments
	print()
	print(args)
	print()
	print(f'article_root = {article_root}')
	print(f'input_root   = {input_root}')
	print(f'output_root  = {output_root}')
	print(f'bad_article  = {bad_article}')
	print()
	print(f'model0       = {model0_cls_name}')
	print(f'model1       = {model1_cls_name}')
	print(f'model0_file  = {model0_file}')
	print(f'model1_file  = {model1_file}')
	print(f'meta_file    = {meta_file}')
	print()

	if args.check: sys.exit()

	############################################################################################################################
	# Load data
	#

	corpus = Corpus(article_root, mention_root=input_root, skip_file=bad_article)
	assert len(corpus.mention_set) > 0
	amsid_list = [m.asmid for m in corpus.mention_set]
	print(f'#mention = {len(amsid_list)}')
	meta   = DataSetMeta.load(meta_file)
	print()

	############################################################################################################################
	# Create model0
	#

	model0 = Model0(meta)
	model0.cuda()
	print()
	print(model0)
	print()
	model0.eval()
	model0.load(model0_file)
	print(f'Loaded model0 from "{model0_file}"')

	############################################################################################################################
	# DataSet of model0
	#

	corpus.reload_mention(input_root)
	ment0_list = MentionList(corpus, [corpus.id_to_mention[asmid] for asmid in amsid_list])
	data0      = model0.ment_data_all(ment0_list)
	dataset0   = torch.utils.data.TensorDataset(*data0.inputs)
	print(f'#mention for model0 = {len(dataset0)}')
	loader0    = torch.utils.data.DataLoader(
		dataset=dataset0,
		batch_size=32,
		shuffle=False,
		drop_last=False,
	)

	############################################################################################################################
	# Predict with model0
	#

	# Apply model
	pred_label0_list = []
	num_step0 = len(loader0)
	pbar0 = tqdm.trange(num_step0, desc=model0_cls_name)
	for _, inputs0_cpu in zip(pbar0, loader0):
		inputs0 = tuple(v.cuda() for v in inputs0_cpu)
		pred_label0_list.append(model0.predict(*inputs0))

	# Concatenate result
	pred_nid0 = model0.label_encoder.inverse_transform(np.concatenate(pred_label0_list))

	############################################################################################################################
	# Create model1
	#

	model1 = Model1(meta)
	model1.cuda()
	print()
	print(model1)
	print()
	model1.eval()
	model1.load(model1_file)
	print(f'Loaded model1 from "{model1_file}"')

	############################################################################################################################
	# DataSet of model1
	#

	corpus.reload_mention(input_root)
	ment1_list = MentionList(corpus, [corpus.id_to_mention[asmid] for asmid in amsid_list])
	data1      = model1.ment_data_all(ment1_list)
	dataset1   = torch.utils.data.TensorDataset(*data1.inputs)
	print(f'#mention for model1 = {len(dataset1)}')
	loader1    = torch.utils.data.DataLoader(
		dataset=dataset1,
		batch_size=32,
		shuffle=False,
		drop_last=False,
	)

	############################################################################################################################
	# Predict with model1
	#

	# Apply model
	pred_label1_list = []
	num_step1 = len(loader1)
	pbar1 = tqdm.trange(num_step1, desc=model1_cls_name)
	for _, inputs1_cpu in zip(pbar1, loader1):
		inputs1 = tuple(v.cuda() for v in inputs1_cpu)
		pred_label1_list.append(model1.predict(*inputs1))

	# Concatenate result
	pred_nid1 = model1.label_encoder.inverse_transform(np.concatenate(pred_label1_list))

	# Merge result
	pred_idx0 = (pred_nid0 != 'PID')
	pred_nid1[pred_idx0] = pred_nid0[pred_idx0]

	############################################################################################################################
	# Writing Results
	#

	del corpus

	corpus    = Corpus(article_root, mention_root=input_root)
	ment_list = MentionList(corpus, [corpus.id_to_mention[asmid] for asmid in amsid_list])
	print(f'#mention for output = {len(ment_list)}')

	# Set NID
	for m, nid in zip(ment_list, pred_nid1):
		m.set_nid(nid)

	# Copy RID(P_rule1) to NID
	for m in ment_list:
		if m.rule == 'P_rule1' and m.rid:
			m.set_nid(m.rid)

	n = str(len(corpus.mention_bundle_set))
	for i, bundle in enumerate(corpus.mention_bundle_set):
		output_file = transform_path(bundle.path, input_root, output_root, '.json')
		printr(f'{i+1:0{len(n)}}/{n}\t{output_file}')
		bundle.save(output_file)
	print()

	pass
