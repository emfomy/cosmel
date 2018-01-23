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

if __name__ == '__main__':

	json_path  = 'data/html/article_filtered'
	html_path  = 'data/html/html_article'
	parts      = ['']

	# Extract html from json
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
							f'''<title>{json_data['title']}</title>''',
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

	pass
