#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import html
import json
import os
import re
import sys

from bs4 import BeautifulSoup

os.chdir(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.abspath('.'))
from styleme import *

def get_html_idx(html_data, html_idx, word):
	try:
		return html_data[html_idx:].index(word)+html_idx
	except ValueError:
		return html_idx

if __name__ == '__main__':

	extracted = False
	parsed    = True
	replaced  = False

	json_root    = f'data/html/article_filtered'
	html_root    = f'data/html/html_article'
	article_root = f'data/article/original_article'
	notag_root   = f'data/html/html_article_notag'
	parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))

	# Extract html from json
	if not extracted:
		for json_file in grep_files(json_root, parts):
			html_dir = json_file.replace(json_root, html_root)
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
								f'''<center>{html.escape(json_data['title'])}</center>''',
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
		print()

	# Parse html
	if not parsed:
		for html_file in grep_files(html_root, parts):
			article_file = html_file.replace(html_root, article_root).replace('.html', '.txt')
			os.makedirs(os.path.dirname(article_file), exist_ok=True)
			printr(article_file)
			with open(html_file) as fin, open(article_file, 'w') as fout:
				soup = BeautifulSoup(fin.read(), 'lxml')
				for s in soup(['script', 'style']): s.decompose()
				fout.write(soup.get_text())
		print()

	# Replace html tags
	if not replaced:
		def repl(m): return '□' * len(m.group())
		regex = re.compile('<[^<>]*?>')
		for html_file in grep_files(html_root, parts):
			notag_file = html_file.replace(html_root, notag_root)
			os.makedirs(os.path.dirname(notag_file), exist_ok=True)
			printr(notag_file)
			with open(html_file) as fin, open(notag_file, 'w') as fout:
				fout.write(regex.sub(repl, fin.read().lower()))
		print()

	pass
