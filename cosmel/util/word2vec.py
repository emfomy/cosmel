#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import math
import os
import sys
import tqdm

from gensim.models.word2vec  import Word2Vec
from gensim.models.callbacks import CallbackAny2Vec

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *


def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Word2Vec.')

	argparser.add_argument('-c', '--corpus', required=True,
			help='store corpus data in directory "<CORPUS>/"')
	argparser.add_argument('-t', '--thread', type=int, \
			help='use <THREAD> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	corpus_root = os.path.normpath(args.corpus)

	nth = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print(f'Use {nth} threads')

	target       = f'purged_article'
	dim          = 300
	repo_root    = f'{corpus_root}/repo'
	article_root = f'{corpus_root}/article/{target}_role'
	emb_file     = f'{corpus_root}/embedding/{target}.dim{dim}.emb.bin'
	parts        = ['']
	# parts        = sorted(rm_ext_all(file) for file in os.listdir(article_root))

	repo     = Repo(repo_root)
	articles = ArticleSet(article_root, parts=parts)
	model    = Word2Vec(sg=1, size=dim, window=10, workers=nth, negative=10, iter=15)

	############################################################################################################################
	# Build vocabulary
	#

	N = 10
	word_count = dict()

	# Brand Name
	n = str(len(repo.brand_set))
	for i, b in enumerate(repo.brand_set):
		printr(f'{i+1:0{len(n)}}/{n}\tBuilding lexicon: {b}')
		for x in b:
			word_count[x] = N
	print()

	# Infix Name
	n = str(len(repo.infix_set))
	for i, x in enumerate(repo.infix_set):
		printr(f'{i+1:0{len(n)}}/{n}\tBuilding lexicon: {x}')
		word_count[x] = N
	print()

	# Head Name
	n = str(len(repo.head_set))
	for i, x in enumerate(repo.head_set):
		printr(f'{i+1:0{len(n)}}/{n}\tBuilding lexicon: {x}')
		word_count[x] = N
	print()

	# Train on vocabulary
	model.build_vocab_from_freq(word_count)

	############################################################################################################################
	# Train on corpus
	#

	sentences = []

	# Product Name
	n = str(len(repo.product_set))
	for i, p in enumerate(repo.product_set):
		printr(f'{i+1:0{len(n)}}/{n}\tBuilding corpus: {p}')
		for x in p.brand:
			for _ in range(N):
				sentences.append([x] + list(p.name_ws.txts))
	print()

	# Product Description
	n = str(len(repo.product_set))
	for i, p in enumerate(repo.product_set):
		printr(f'{i+1:0{len(n)}}/{n}\tBuilding corpus: {p}')
		for _ in range(N):
			sentences.append(list(p.descr_ws.txts))
	print()

	# Article Corpus
	n = str(len(articles))
	for i, article in enumerate(articles):
		printr(f'{i+1:0{len(n)}}/{n}\tBuilding corpus: {article.aid}')
		sentences += [list(sentence.txts) for sentence in article]
	print()

	# Training
	model.build_vocab(sentences, update=True)
	word2vec_train(model, sentences)

	# Save embedding
	os.makedirs(os.path.dirname(emb_file), exist_ok=True)
	model.wv.save_word2vec_format(emb_file, binary=True)
	print(f'Output Word2Vec embedding to "{emb_file}"')


def word2vec_train(model, sentences):

	# Training
	class ProgressBar(CallbackAny2Vec):
		def __init__(self, model, total_words):
			self.epochs = model.epochs
			self.batchs = total_words // model.batch_words
			self.epoch  = 0

		def on_epoch_begin(self, model):
			self.pbar = tqdm.trange(self.batchs, desc=f'Epoch {self.epoch+1:0{len(str(self.epochs))}}/{self.epochs}')

		def on_epoch_end(self, model):
			self.epoch += 1

		def on_batch_begin(self, model):
			self.pbar.update()

		def on_batch_end(self, model):
			pass

	total_words = sum(len(sentence) for sentence in sentences)

	model.train(sentences, total_words=total_words, epochs=model.epochs, callbacks=[ProgressBar(model, total_words)])

if __name__ == '__main__':

	main()
	print()
	pass
