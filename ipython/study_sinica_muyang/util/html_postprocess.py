#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import json
import os
import sys

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

def get_html_idx(html_data, word, start_idx):
	try:
		return html_data[(start_idx+1):].index(word)+(start_idx+1)
	except ValueError:
		return start_idx

if __name__ == '__main__':

	assert len(sys.argv) > 1
	ver = sys.argv[1]


	target       = f'pruned_article'
	data_root    = f'data/{ver}'
	article_root = f'{data_root}/article/{target}_role'
	html_root    = f'{data_root}/html/html_article_notag'
	idx_root     = f'{data_root}/html/{target}_idx'
	parts        = ['']
	parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) > 2: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	# Map word-segmented articles to html articles
	html_files = grep_files(html_root, parts=parts)
	n = str(len(html_files))
	for i, html_file in enumerate(html_files):
		idx_file = transform_path(html_file, html_root, idx_root, '.idx')
		os.makedirs(os.path.dirname(idx_file), exist_ok=True)
		printr(f'{i+1:0{len(n)}}/{n}\t{idx_file}')

		article_file = transform_path(html_file, html_root, article_root, '.role')
		article = Article(article_file)

		with open(html_file) as fin, open(idx_file, 'w') as fout:
			html_data = fin.read()
			html_idx = -1
			for sid, line in enumerate(article):
				idx_line_list = []
				for mid, word in enumerate(line.txts):
					chars = ''.join(word.replace('□', ''))
					char = chars[0]
					html_idx = get_html_idx(html_data, char, html_idx)
					html_idx0 = html_idx
					for char in chars[1:]:
						html_idx = get_html_idx(html_data, char, html_idx)
					idx_line_list.append(f'{word}({html_idx0},{html_idx})')
				fout.write('　'.join(idx_line_list)+'\n')
	print()

	pass
