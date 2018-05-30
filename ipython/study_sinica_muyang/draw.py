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

from styleme import *


if __name__ == '__main__':

	assert len(sys.argv) == 2
	ver = sys.argv[1]

	target       = f'pruned_article'
	target_ver   = f'_pid'
	data_root    = f'data/{ver}'
	repo_root    = f'{data_root}/repo'
	emb_file     = f'{data_root}/embedding/pruned_article{target_ver}.dim300.emb.bin'

	repo = Repo(repo_root)
	from gensim.models.keyedvectors import KeyedVectors
	keyed_vectors = KeyedVectors.load_word2vec_format(emb_file, binary=True)

	############################################################################################################################
	# Draw
	#

	from sklearn.decomposition import PCA
	from sklearn.manifold import TSNE

	words = np.asarray(['PID'+p.pid for p in repo.product_set])

	embs  = keyed_vectors[words]
	pca   = PCA(n_components=2)
	embr  = pca.fit_transform(embs)
	products = np.asarray(list(repo.product_set))

	bad_idxs  = (embr[:, 0] < -0.5)
	good_idxs = np.logical_not(bad_idxs)

	choose_head = ['精華', '面膜', '唇膏', '睫毛膏', '蜜粉', '眼霜', '化妝水', '乳液', '粉餅', '乳霜']
	choose_idxs = good_idxs & np.asarray([(p.head in choose_head) for p in products])

	words = words[bad_idxs]
	embs  = embs[bad_idxs, :]
	products = products[bad_idxs]
	# tsne  = TSNE(n_components=2)
	# embr  = tsne.fit_transform(embs)
	pca   = PCA(n_components=2)
	embr  = pca.fit_transform(embs)

	from matplotlib.font_manager import FontProperties
	font = FontProperties(fname='/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf', size=8)

	markers = ('o', 'v', '^', '<', '>', '8', 's', 'p', '*', 'h', 'H', 'D', 'd', 'P', 'X')

	from collections import Counter

	labels  = repo.head_set
	idxs    = [[i for i, p in enumerate(products) if p.head == h] for h in repo.head_set]
	counter = Counter([p.head for p in products])

	# labels  = [b[0] for b in repo.brand_set]
	# idxs    = [[i for i, p in enumerate(products) if p.brand == b] for b in repo.brand_set]
	# counter = Counter([p.brand[0] for p in products])

	labels_most = [h for h, _ in counter.most_common(10)]
	colors      = cm.rainbow(np.linspace(0, 1, len(labels)))

	fig = plt.figure(figsize=(8, 8))
	ax = plt.subplot(111)
	# ax = plt.subplot(111, projection='3d')

	mit     = iter(markers)
	handles = ([], [],)
	for h, c, ii in zip(labels, colors, idxs):
		printr(h)
		if ii:
			handle = ax.scatter(embr[ii, 0], embr[ii, 1], c=c, marker='.', label=h)
	# 	if h in labels_most:
	# 		handle = ax.scatter(embr[ii, 0], embr[ii, 1], c=c, marker=next(mit), label=h)
	# 		handles[0].append(handle)
	# 		handles[1].append(h)
	# plt.legend(*handles, loc='upper center', bbox_to_anchor=(1,1), prop=font)

	fig.savefig('plot.jpg')

	pass
