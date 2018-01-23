#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import json
import os
import sys

os.chdir(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.abspath('.'))
from styleme import *

def get_html_idx(html_data, html_idx, word):
	try:
		return html_data[html_idx:].index(word)+html_idx
	except ValueError:
		return html_idx

if __name__ == '__main__':

	extracted = True
	indexed   = True

	article_dir  = f'prune_article_ws'
	repo_path    = f'data/repo'
	article_path = f'data/article/{article_dir}'
	json_path    = f'data/html/article_filtered'
	html_path    = f'data/html/html_article'
	idx_path     = f'data/html/{article_dir}_idx'
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = ['']

	# Extract html from json
	if not extracted:
		for json_file in grep_files(json_path, parts):
			html_dir = json_file.replace(json_path, html_path)
			os.makedirs(html_dir, exist_ok=True)
			with open(json_file) as fin:
				for line in fin:
					json_data = json.loads(line)
					html_data = '\n'.join([
						'<!DOCTYPE html>',
						'<html>',
							'<head>',
								'<meta charset="UTF-8">',
							'</head>',
							'<body>',
								f'''<center>{json_data['title']}</center>''',
								'<hr>',
								json_data['content'],
							'</body>',
						'</html>',
					])
					a_id = json_data['author'] + '_' + json_data['article_id']
					html_file = f'{html_dir}/{a_id}.html'
					printr(html_file)
					with open(html_file, 'w') as fout:
						fout.write(html_data)

	# Map word-segmented articles to html articles
	if not indexed:
		for html_file in grep_files(html_path, parts):
			idx_file     = html_file.replace(html_path, idx_path).replace('.html', '.txt.idx')
			os.makedirs(os.path.dirname(idx_file), exist_ok=True)
			printr(idx_file)

			article_file = html_file.replace(html_path, article_path).replace('.html', '.txt.tag')
			article = Article(article_file)

			with open(html_file) as fin, open(idx_file, 'w') as fout:
				html_data = fin.read().lower()
				html_idx = 0
				for s_id, line in enumerate(article):
					idx_line_list = []
					for m_id, word in enumerate(line.txts):
						chars = ''.join(word.replace('□', ''))
						char = chars[0]
						html_idx = get_html_idx(html_data, html_idx, char)
						idx_line_list.append(f'{word}({html_idx})')
						for char in chars[1:]:
							html_idx = get_html_idx(html_data, html_idx, char)
					fout.write('　'.join(idx_line_list)+'\n')

	pass
