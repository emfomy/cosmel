#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
   Mu Yang <emfomy@gmail.com>
"""

import itertools
import os
import sys

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

from xml_encode import add_xml

def get_html_idxs(mention):
	return (int(mention.sentence.tags[mention.brand_idx].split(',')[0]), \
			int(mention.sentence.tags[mention.head_idx].split(',')[1]))

if __name__ == '__main__':

	assert len(sys.argv) >= 2
	ver = sys.argv[1]

	target       = f'prune_article_ws_pid'
	data_root    = f'data/{ver}'
	repo_root    = f'{data_root}/repo'
	idx_root     = f'{data_root}/html/prune_article_ws_idx'
	article_root = f'{data_root}/article/prune_article_ws'
	mention_root = f'{data_root}/mention/{target}'
	html_root    = f'{data_root}/html/html_article'
	output_root  = f'{data_root}/html/{target}'
	parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	# parts        = list(f'part-{x:05}' for x in range(128) if x % 8 == int(sys.argv[2]))

	# Load StyleMe repository and corpus
	repo   = Repo(repo_root)
	corpus = Corpus(article_root, mention_root, repo, parts=parts)
	corpus_idx = Corpus(idx_root, mention_root, repo, parts=parts)

	# Extract html from json
	for html_file in grep_files(html_root, parts):
		output_file = html_file.replace(html_root, output_root).replace('.html', '.xml.html')
		os.makedirs(os.path.dirname(output_file), exist_ok=True)
		printr(output_file)

		with open(html_file) as fin, open(output_file, 'w') as fout:
			output_data = list(fin.read())
			bundle = corpus.id_to_mention_bundle[Article.path_to_a_id(html_file)]

			for mention in bundle:
				idx0, idx1 = get_html_idxs(corpus_idx.id_to_mention[mention.ids])
				output_data[idx0], output_data[idx1] = add_xml(
						output_data[idx0], output_data[idx1], mention, repo
				)

			fout.write(''.join(output_data))
	print()

	pass
