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
	repo_path    = f'data/repo'
	article_path = f'data/html/prune_article_ws_idx'
	mention_path = f'data/mention/{mention_dir}'
	html_path    = f'data/html/html_article'
	output_path  = f'data/html/{mention_dir}'
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = ['']

	# Load StyleMe repository and corpus
	repo   = Repo(repo_path)
	corpus = Corpus(article_path, mention_path, repo, parts=parts)

	# Extract html from json
	for html_file in grep_files(html_path, parts):
		output_file = html_file.replace(html_path, output_path).replace('.html', '.xml.html')
		os.makedirs(os.path.dirname(output_file), exist_ok=True)
		printr(output_file)

		with open(html_file) as fin, open(output_file, 'w') as fout:
			output_data = list(fin.read())
			article_file = html_file.replace(html_path, article_path).replace('.html', '.txt.tag')
			article = corpus.path_to_article[article_file]
			bundle  = corpus.article_to_mention_bundle[article]

			for mention in bundle:
				idx0, idx1 = get_html_idxs(mention)
				output_data[idx0] = \
						f'<product pid="{mention.p_id}" gid="{mention.g_id}" sid="{mention.s_id}" idx="{mention.beginning_idx}">' + \
						output_data[idx0]
				output_data[idx1] += '</product>'

			fout.write(''.join(output_data))
	print()

	pass
