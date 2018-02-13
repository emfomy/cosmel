#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
   Mu Yang <emfomy@gmail.com>
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

def get_html_idx(html_data, html_idx, word):
	try:
		return html_data[html_idx:].index(word)+html_idx
	except ValueError:
		return html_idx

if __name__ == '__main__':

	assert len(sys.argv) >= 2
	ver = sys.argv[1]


	target       = f'prune_article_ws'
	data_root    = f'data/{ver}'
	article_root = f'{data_root}/article/{target}'
	html_root    = f'{data_root}/html/html_article_notag'
	idx_path     = f'{data_root}/html/{target}_idx'
	parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	# parts        = list(f'part-{x:05}' for x in range(128) if x % 8 == int(sys.argv[2]))

	# Map word-segmented articles to html articles
	for html_file in grep_files(html_root, parts):
		idx_file     = html_file.replace(html_root, idx_path).replace('.html', '.txt.tag')
		os.makedirs(os.path.dirname(idx_file), exist_ok=True)
		printr(idx_file)

		article_file = html_file.replace(html_root, article_root).replace('.html', '.txt.tag')
		article = Article(article_file)

		with open(html_file) as fin, open(idx_file, 'w') as fout:
			html_data = fin.read()
			html_idx = 0
			for s_id, line in enumerate(article):
				idx_line_list = []
				for m_id, word in enumerate(line.txts):
					chars = ''.join(word.replace('□', ''))
					char = chars[0]
					html_idx = get_html_idx(html_data, html_idx, char)
					html_idx0 = html_idx
					for char in chars[1:]:
						html_idx = get_html_idx(html_data, html_idx, char)
					idx_line_list.append(f'{word}({html_idx0},{html_idx})')
				fout.write('　'.join(idx_line_list)+'\n')
	print()

	pass
