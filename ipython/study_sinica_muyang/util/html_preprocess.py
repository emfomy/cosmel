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

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

def get_html_idx(html_data, html_idx, word):
	try:
		return html_data[html_idx:].index(word)+html_idx
	except ValueError:
		return html_idx

if __name__ == '__main__':

	extracted = False
	replaced  = False
	parsed    = False

	assert len(sys.argv) >= 2
	ver = sys.argv[1]

	etc_root     = f'etc'
	data_root    = f'data/{ver}'
	json_root    = f'{data_root}/html/article_filtered'
	html_root    = f'{data_root}/html/html_article'
	article_root = f'{data_root}/article/original_article'
	notag_root   = f'{data_root}/html/html_article_notag'
	parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = list(f'part-{x:05}' for x in range(128) if x % 8 == int(sys.argv[2]))

	# Extract html from json
	if not extracted:
		for json_file in grep_files(json_root, parts):
			html_dir = json_file.replace(json_root, html_root)
			os.makedirs(html_dir, exist_ok=True)
			with open(json_file) as fin:
				for line in fin:
					json_data = json.loads(line)
					a_id = json_data['author'] + '_' + json_data['article_id']
					if a_id in ['imsandra_28191442', 'imsandra_28166295', 'imsandra_28209327', 'imsandra_28096303']:
						with open(f'{etc_root}/{a_id}.json') as f:
							json_data = json.load(f)

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
					html_file = f'{html_dir}/{a_id}.html'
					printr(html_file)
					with open(html_file, 'w') as fout:
						soup = BeautifulSoup(html_data, 'lxml')
						fout.write(soup.prettify())
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

	# Parse html
	if not parsed:
		regexes0 = [(re.compile('[^\S ]'), ' ')]
		for tag in ['blockquote', 'center', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre']:
			regexes0.append((re.compile(rf'<{tag}>'), f'\n<{tag}>'))
			regexes0.append((re.compile(rf'</{tag}>'), f'</{tag}>\n'))
		for tag in ['br', 'hr']:
			regexes0.append((re.compile(rf'<{tag}/>'), f'<{tag}/>\n'))

		regexes1 = [ \
				(re.compile(r' +'), ' '), \
				(re.compile(r' ($|\n)'), '\n'), \
				(re.compile(r'(\A|\n) '), '\n'), \
				(re.compile(r'\n+'), '\n'), \
		]

		for html_file in grep_files(html_root, parts):
			article_file = html_file.replace(html_root, article_root).replace('.html', '.txt')
			os.makedirs(os.path.dirname(article_file), exist_ok=True)
			printr(article_file)
			with open(html_file) as fin, open(article_file, 'w') as fout:
				html_data = fin.read()
				for regex in regexes0:
					html_data = regex[0].sub(regex[1], html_data)

				soup = BeautifulSoup(html_data, 'lxml')
				for s in soup(['script', 'style']): s.decompose()

				text_data = soup.text.strip()+'\n'
				for regex in regexes1:
					text_data = regex[0].sub(regex[1], text_data)
				fout.write(text_data)
		print()

	pass
