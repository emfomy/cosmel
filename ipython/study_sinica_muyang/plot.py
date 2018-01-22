#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

from styleme import *


if __name__ == '__main__':

	# repo = Repo('data/repo')

	# Load data
	data  = numpy.loadtxt('data/tmp/entity.emb').T
	with open('data/tmp/label.txt') as fin: label = fin.read().splitlines()
	pca = PCA(n_components=2)
	data_r = pca.fit_transform(data)

	plt.figure(figsize=(8, 8))
	for i, l in enumerate(label):
		x = data_r[i, 0]
		y = data_r[i, 1]
		plt.scatter(x, y)
		plt.annotate(l, xy=(x, y), xytext=(5, 2), textcoords='offset points', ha='right', va='bottom')
	plt.title('PCA')
	plt.savefig('data/tmp/plot.jpg')

	pass
