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

def add_start_xml(start, mention):
	return mention.start_xml + start

def add_end_xml(end, mention):
	return end + mention.end_xml

if __name__ == '__main__':

	assert len(sys.argv) >= 2
	ver = sys.argv[1]

	target       = f'pruned_article'
	target_ver   = f''
	# target_ver   = f'_pid'
	target_ver   = f'_exact'
	data_root    = f'data/{ver}'
	repo_root    = f'{data_root}/repo'
	article_root = f'{data_root}/article/{target}_ws'
	mention_root = f'{data_root}/mention/{target}{target_ver}'
	xml_path     = f'{data_root}/xml/{target}{target_ver}'
	parts         = ['']
	parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) >= 3: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	# Load StyleMe repository and corpus
	corpus = Corpus(article_root, mention_root, parts=parts)

	# Extract html from json
	n = str(len(corpus.mention_bundle_set))
	for i, bundle in enumerate(corpus.mention_bundle_set):
		article = bundle.article
		xml_file = transform_path(article.path, article_root, xml_path, '.xml')
		os.makedirs(os.path.dirname(xml_file), exist_ok=True)
		printr(f'{i+1:0{len(n)}}/{n}\t{xml_file}')
		with open(xml_file, 'w') as fout:
			for mention in bundle:
				article[mention.s_id].txts[mention.start_idx] = add_start_xml(article[mention.s_id].txts[mention.start_idx], mention)
				article[mention.s_id].roles[mention.last_idx] = add_end_xml(article[mention.s_id].roles[mention.last_idx], mention)
			fout.write(roledstr(article))
	print()

	pass
