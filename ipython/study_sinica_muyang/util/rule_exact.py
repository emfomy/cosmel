#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import itertools
import os
import sys
import time

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

def decision_tree(mention, repo):

	# Find brand
	try:
		b_idx  = mention.m_id - 1 - list(reversed(mention.sentence_pre.roles)).index('Brand')
		b_name = mention.sentence.txts[b_idx]
	except ValueError:
		return

	candidates = repo.b_name_head_to_product_list[b_name, mention.head]
	m_name = ''.join(mention.sentence_pre.txts[b_idx+1:])

	# Exact --- exact match
	for i, candidate in enumerate(candidates):
		if m_name == txtstr(candidate.infix_ws):
			mention.set_rule('exact')
			mention.set_p_id(candidate.p_id)
			return


if __name__ == '__main__':

	assert len(sys.argv) >= 2
	ver = sys.argv[1]

	target       = f'pruned_article'
	data_root    = f'data/{ver}'
	repo_root    = f'{data_root}/repo'
	article_root = f'{data_root}/article/{target}_role'
	mention_root = f'{data_root}/mention/{target}'
	output_root  = f'{data_root}/mention/{target}_exact'
	parts        = ['']
	parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) >= 3: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	repo   = Repo(repo_root)
	corpus = Corpus(article_root, mention_root, parts=parts)

	# Process rules
	for bundle in corpus.mention_bundle_set:
		printr(f'Processing {bundle.path}')

		# Run rules
		previous_products = set()
		for mention in bundle:

			# Run decision tree
			decision_tree(mention, repo)

			# Display result
			# if mention.p_id: print('\t'.join([str(mention.ids), mention.rule, str(mention.sentence)]))

	print()

	# Save data
	corpus.mention_bundle_set.save(output_root)

	pass
