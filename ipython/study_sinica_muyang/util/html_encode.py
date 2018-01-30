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

def get_html_idxs(mention):
	return (int(mention.sentence.tags[mention.brand_idx].split(',')[0]), \
			int(mention.sentence.tags[mention.head_idx].split(',')[1]))

if __name__ == '__main__':

	mention_dir  = f'prune_article_ws'
	repo_root    = f'data/repo'
	article_root = f'data/html/prune_article_ws_idx'
	mention_root = f'data/mention/{mention_dir}'
	html_root    = f'data/html/html_article'
	output_root  = f'data/html/{mention_dir}'
	parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))

	# Load StyleMe repository and corpus
	repo   = Repo(repo_root)
	corpus = Corpus(article_root, mention_root, repo, parts=parts)

	# Extract html from json
	for html_file in grep_files(html_root, parts):
		output_file = html_file.replace(html_root, output_root).replace('.html', '.xml.html')
		os.makedirs(os.path.dirname(output_file), exist_ok=True)
		printr(output_file)

		with open(html_file) as fin, open(output_file, 'w') as fout:
			output_data = list(fin.read())
			article = corpus.id_to_article[Article.path_to_a_id(html_file)]
			bundle  = corpus.article_to_mention_bundle[article]

			for mention in bundle:
				idx0, idx1 = get_html_idxs(mention)
				output_data[idx0] = mention.beginning_xml + output_data[idx0]
				output_data[idx1] += mention.ending_xml

			fout.write(''.join(output_data))
	print()

	pass
