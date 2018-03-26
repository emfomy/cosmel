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

	if mention.head_role != 'PName': return
	if mention.mid == 0: return

	b_idx = mention.mid-1
	if mention.sentence.roles[b_idx] != 'Brand': return

	bname = mention.sentence.txts[b_idx]
	m_name = mention.head
	try:
		candidate = repo.bname_pname_to_product[bname, m_name]
	except KeyError:
		return

	# Exact --- exact match
	if m_name == candidate.name:
		mention.set_rule('exact')
		mention.set_pid(candidate.pid)
		return


if __name__ == '__main__':

	assert len(sys.argv) > 1
	ver = sys.argv[1]

	target       = f'pruned_article'
	data_root    = f'data/{ver}'
	repo_root    = f'{data_root}/repo'
	article_root = f'{data_root}/article/{target}_role'
	mention_root = f'{data_root}/mention/{target}'
	output_root  = f'{data_root}/mention/{target}_exact'
	parts        = ['']
	parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) > 2: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

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
			# if mention.pid: print('\t'.join([str(mention.ids), mention.rule, str(mention.sentence)]))

	print()

	# Save data
	corpus.mention_bundle_set.save(output_root)

	pass
