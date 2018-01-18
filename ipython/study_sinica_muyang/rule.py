#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import os
import time

from styleme import *

def relu(x):
	return max(x, 0)

def decision_tree(mention, repo, previous_products):
	candidates = repo.brandhead_to_product_list[(mention.brand, mention.head)]

	mention_descri_set       = set(mention.descri_ws.txts)
	mention_descri_no_de_set = mention_descri_set - set('的')

	candidate_descri_sets = [set(candidate.descri_ws.txts + candidate.suffix_ws.txts) for candidate in candidates]
	candidate_descri_no_de_sets = [candidate_descri_set - set('的') for candidate_descri_set in candidate_descri_sets]

	# Exact --- exact match
	for i, candidate in enumerate(candidates):
		if candidate.name == mention.name:
			mention.set_rule('exact')
			mention.set_p_id(candidate.p_id)
			return

	# Rule 1a --- mention's description is a subset of the candidate's
	if len(mention_descri_set) > 0:
		for i, candidate in enumerate(candidates):
			if mention_descri_set <= candidate_descri_sets[i]:
				mention.set_rule('1a')
				mention.set_p_id(candidate.p_id)
				return

	# Rule 1b --- mention's description is a subset of the candidate's (excluding "的")
	if len(mention_descri_no_de_set) > 0:
		for i, candidate in enumerate(candidates):
			if mention_descri_no_de_set <= candidate_descri_no_de_sets[i]:
				mention.set_rule('1b')
				mention.set_p_id(candidate.p_id)
				return

	# Rule 2 --- mention has leading "這" in 5 terms
	if '這' in mention.sentence.txts[relu(mention.beginning_idx-5):mention.beginning_idx]:

		# Rule 2a
		for i, candidate in enumerate(candidates):
			if candidate in previous_products:
				mention.set_rule('2a')
				mention.set_p_id(candidate.p_id)
				return

		# Rule 2b
		mention.set_rule('2b')
		mention.set_p_id('OSP')
		return

	# Rule 3 --- mention has leading "一Nf"
	if '一' == mention.sentence.txts[relu(mention.beginning_idx-2)] and \
			'Nf' == mention.sentence.tags[relu(mention.beginning_idx-1)]:
		# Rule 3c
		if '另' == mention.sentence.tags[relu(mention.beginning_idx-3)] or \
				'另外' in mention.sentence.tags[relu(mention.beginning_idx-3)]:
			mention.set_rule('2b')
			mention.set_p_id('OSP')
			return

		# Rule 3a
		for i, candidate in enumerate(candidates):
			if candidate in previous_products:
				mention.set_rule('2a')
				mention.set_p_id(candidate.p_id)
				return

		# Rule 3b
		mention.set_rule('2b')
		mention.set_p_id('OSP')
		return

	# Rule 101 --- mention has no description
	if len(mention_descri_set) == 0:
		mention.set_rule('100a')
		mention.set_p_id('GP')
		return

	# Rule 101 --- mention contains "的"
	if '的' in mention_descri_set:
		mention.set_rule('101a')
		mention.set_p_id('GP')
		return

	# Nil --- no candidate
	if len(candidates) == 0:
		mention.set_rule('nil')
		mention.set_p_id('NAP')
		return

	# Else
	mention.set_rule('else')
	mention.set_p_id('NAP')
	return


if __name__ == '__main__':

	date          = time.strftime("%Y%m%d.%H%M%S")
	repo_path     = 'data/repo'
	article_path  = 'data/article/prune_article_ws'
	mention_path  = 'data/mention/prune_article_ws'
	output_path   = 'data/mention/prune_article_ws_pid_'+date

	repo   = Repo(repo_path)
	corpus = Corpus(article_path, mention_path, repo)

	previous_product_rules = set(['exact', '1a', '1b'])
	for article in corpus.article_set:
		bundle = article_to_mention_bundle[article]
		printr('Processing {}'.format(bundle.path))

		# Run rules
		previous_products = set()
		for mention in bundle:

			# Run decision tree
			decision_tree(mention, repo, previous_products)

			# Update previous product
			if mention.rule in previous_product_rules:
				previous_products.add(repo.id_to_product[mention.p_id])

			# Display result
			# print('\t'.join([mention.p_id, mention.rule, str(mention.sentence)]))
			# if mention.p_id.isdigit(): print(repr(repo.id_to_product[mention.p_id]))

		# Save data
		output_file = bundle.path.replace(mention_path, output_path)
		bundle.save(output_file)
	print()

	pass
