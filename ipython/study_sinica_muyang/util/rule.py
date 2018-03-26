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

def decision_tree(mention, repo, previous_products):
	candidates = list(itertools.chain.from_iterable(
			repo.brand_head_to_product_list[mention.brand, head] for head in reversed(mention.head_list)
	))

	mention_affix_set       = set(mention.infix_ws.txts)
	mention_affix_no_de_set = mention_affix_set - set('的')

	candidate_affix_sets       = [set(candidate.infix_ws.txts + candidate.suffix_ws.txts) for candidate in candidates]
	candidate_affix_no_de_sets = [candidate_affix_set - set('的') for candidate_affix_set in candidate_affix_sets]

	# Exact --- exact match
	for i, candidate in enumerate(candidates):
		if candidate.name == mention.name:
			mention.set_rule('exact')
			mention.set_pid(candidate.pid)
			return

	# Rule 1a --- mention's infix is a subset of the candidate's
	if len(mention_affix_set) > 0:
		for i, candidate in enumerate(candidates):
			if mention_affix_set <= candidate_affix_sets[i]:
				mention.set_rule('01a')
				mention.set_pid(candidate.pid)
				return

	# Rule 1b --- mention's infix is a subset of the candidate's (excluding "的")
	if len(mention_affix_no_de_set) > 0:
		for i, candidate in enumerate(candidates):
			if mention_affix_no_de_set <= candidate_affix_no_de_sets[i]:
				mention.set_rule('01b')
				mention.set_pid(candidate.pid)
				return

	# Rule 2 --- mention has leading "這" in 5 terms
	if '這' in mention.sentence.txts[relu(mention.start_idx-5):mention.start_idx]:

		# Rule 2a
		for i, candidate in enumerate(candidates):
			if candidate in previous_products:
				mention.set_rule('02a')
				mention.set_pid(candidate.pid)
				return

		# Rule 2b
		mention.set_rule('02b')
		mention.set_pid('OSP')
		return

	# Rule 3 --- mention has leading "一Nf"
	if '一' == mention.sentence.txts[relu(mention.start_idx-2)] and \
			'Nf' == mention.sentence.tags[relu(mention.start_idx-1)]:
		# Rule 3c
		if '另' == mention.sentence.txts[relu(mention.start_idx-3)] or \
				'另外' in mention.sentence.txts[relu(mention.start_idx-3)]:
			mention.set_rule('03b')
			mention.set_pid('OSP')
			return

		# Rule 3a
		for i, candidate in enumerate(candidates):
			if candidate in previous_products:
				mention.set_rule('03a')
				mention.set_pid(candidate.pid)
				return

		# Rule 3b
		mention.set_rule('03b')
		mention.set_pid('OSP')
		return

	# Rule 51 --- mention has no infix
	if len(mention_affix_set) == 0:
		mention.set_rule('50a')
		mention.set_pid('GP')
		return

	# Rule 51 --- mention contains "的"
	if '的' in mention_affix_set:
		mention.set_rule('51a')
		mention.set_pid('GP')
		return

	# Nil --- no candidate
	if len(candidates) == 0:
		mention.set_rule('nil')
		mention.set_pid('NAP')
		return

	# Else
	mention.set_rule('else')
	mention.set_pid('NAP')
	return


if __name__ == '__main__':

	assert len(sys.argv) > 1
	ver = sys.argv[1]

	target       = f'pruned_article'
	data_root    = f'data/{ver}'
	repo_root    = f'{data_root}/repo'
	article_root = f'{data_root}/article/{target}_role'
	mention_root = f'{data_root}/mention/{target}'
	output_root  = f'{data_root}/mention/{target}_pid'
	parts        = ['']
	parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) > 2: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	repo   = Repo(repo_root)
	corpus = Corpus(article_root, mention_root, parts=parts)

	# Process rules
	previous_product_rules = set(['exact', '01a', '01b'])
	for bundle in corpus.mention_bundle_set:
		printr(f'Processing {bundle.path}')

		# Run rules
		previous_products = set()
		for mention in bundle:

			# Run decision tree
			decision_tree(mention, repo, previous_products)

			# Update previous product
			if mention.rule in previous_product_rules:
				previous_products.add(repo.id_to_product[mention.pid])

			# Display result
			# print('\t'.join([mention.pid, mention.rule, str(mention.sentence)]))
			# if mention.pid.isdigit(): print(repr(repo.id_to_product[mention.pid]))

	print()

	# Save data
	corpus.mention_bundle_set.save(output_root)

	pass
