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
	target       = f'pixnet_article'
	target_ver   = f''
	# target_ver   = f'_pid'
	# target_ver   = f'_exact'
	target_ver   = f'_gid'
	data_root    = f'data/{ver}'
	repo_root    = f'{data_root}/repo'
	article_root = f'{data_root}/article/{target}_role'
	mention_root = f'{data_root}/mention/{target}{target_ver}'
	xml_root     = f'{data_root}/xml/{target}{target_ver}'
	parts         = ['']
	parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) >= 3: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	# Extract html from json
	mention_files = grep_files(mention_root, parts)
	n = str(len(mention_files))
	for i, mention_file in enumerate(mention_files):
		article_file = transform_path(mention_file, mention_root, article_root, '.role')
		article = Article(article_file)
		bundle = MentionBundle(mention_file, article)
		xml_file = transform_path(article.path, article_root, xml_root, '.xml')

		os.makedirs(os.path.dirname(xml_file), exist_ok=True)
		printr(f'{i+1:0{len(n)}}/{n}\t{xml_file}')

		for mention in bundle:
			article[mention.sid].txts[mention.start_idx] = add_start_xml(article[mention.sid].txts[mention.start_idx], mention)
			article[mention.sid].txts[mention.last_idx]  = add_end_xml(article[mention.sid].txts[mention.last_idx],    mention)

		article.save(xml_file, txtstr)
	print()

	pass
