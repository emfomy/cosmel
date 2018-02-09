#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import os
import sys

os.chdir(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.abspath('.'))
from styleme import *

def add_xml(beginning, ending, mention, repo):
	candidates = list(itertools.chain.from_iterable(
			repo.brand_head_to_product_list[mention.brand, head] for head in reversed(mention.head_list)
	))
	return (mention.beginning_xml_(hint=','.join(p.p_id for p in candidates)) + beginning, ending + mention.ending_xml)

if __name__ == '__main__':

	assert len(sys.argv) >= 2
	ver = sys.argv[1]

	target       = f'prune_article_ws_pid'
	data_root    = f'data/{ver}'
	repo_root    = f'{data_root}/repo'
	article_root = f'{data_root}/article/prune_article_ws'
	mention_root = f'{data_root}/mention/{target}'
	xml_path     = f'{data_root}/xml/{target}'
	parts         = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	# parts        = list(f'part-{x:05}' for x in range(128) if x % 8 == int(sys.argv[2]))

	# Load StyleMe repository and corpus
	repo   = Repo(repo_root)
	corpus = Corpus(article_root, mention_root, repo, parts=parts)

	# Extract html from json
	for bundle in corpus.mention_bundle_set:
		article = bundle.article
		xml_file = article.path.replace(article_root, xml_path).replace('.txt.tag', '.xml')
		os.makedirs(os.path.dirname(xml_file), exist_ok=True)
		printr(xml_file)
		with open(xml_file, 'w') as fout:
			for mention in bundle:
				article[mention.s_id].txts[mention.brand_idx], article[mention.s_id].txts[mention.head_idx] = add_xml(
						article[mention.s_id].txts[mention.brand_idx], article[mention.s_id].txts[mention.head_idx], mention, repo
				)
			fout.write(txtstr(article))
	print()

	pass
