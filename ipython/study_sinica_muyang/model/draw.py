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

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D

from sklearn.decomposition import PCA

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from styleme import *
from model.module.meta import *


if __name__ == '__main__':

	# Parse arguments
	argparser = argparse.ArgumentParser(description='Draw StyleMe model.')

	arggroup = argparser.add_mutually_exclusive_group()
	arggroup.add_argument('-v', '--ver', metavar='<ver>#<date>', \
			help='set <dir> as "result/<ver>_<date>"')
	arggroup.add_argument('-D', '--dir', metavar='<dir>', \
			help='prepend <dir> to data and model path')

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
	print(f'model_file    = {model_file}')
	print(f'meta_file     = {meta_file}')
	print()

	if args.check: exit()

	############################################################################################################################
	# Create model
	#

	meta = DataSetMeta.load(meta_file)
	model = Model(meta)
	model.cuda()
	print()
	print(model)
	print()
	model.eval()

	############################################################################################################################
	# Draw
	#

	repo = Repo(meta.repo_path)
	embs = model.entity_emb.weight.cpu().data.numpy()
	products = [repo.id_to_product[pid] for pid in meta.p_encoder.classes_]
	pca  = PCA(n_components=3)
	embr = pca.fit_transform(embs)

	# from collections import Counter
	# counter = Counter([p.head for p in repo.product_set])
	# counter.most_common(10)

	# heads = ['面膜', '精華', '唇膏', '睫毛膏', '洗面乳']

	fig = plt.figure(figsize=(8, 8))
	# ax = Axes3D(fig)
	ax = plt

	# heads = repo.head_set
	# heads = ['面膜', '精華', '唇膏', '睫毛膏', '洗面乳']
	# heads = ['面膜', '口紅']
	# colors = cm.rainbow(np.linspace(0, 1, len(heads)))
	# for h, c in zip(heads, colors):
	# 	printr(h)
	# 	idxs = [i for i, p in enumerate(products) if p.head == h]
	# 	# ax.scatter(embr[idxs, 0], embr[idxs, 1], embr[idxs, 2], c=c)
	# 	ax.scatter(embr[idxs, 0], embr[idxs, 1], c=c)

	# bnames = [b[0] for b in repo.brand_set]
	bnames = ['puresmile', 'beautybuffet', 'drwu', 'kosecosmeport', '我的美麗日記']
	colors = cm.rainbow(np.linspace(0, 1, len(bnames)))
	for b, c in zip(bnames, colors):
		printr(b)
		idxs = [i for i, p in enumerate(products) if p.brand == repo.bname_to_brand[b] and p.head == '面膜']
		ax.scatter(embr[idxs, 0], embr[idxs, 1], c=c)

	fig.savefig('plot.jpg')

	pass
