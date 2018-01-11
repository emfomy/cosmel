#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import os
import re
import shutil
import subprocess

from styleme import *


class ReplaceVariant():
	"""The driver of replacing(removing) variants in the article."""

	def __init__(self):
		pass

	def sub(self, chars):
		return chars.encode('big5', errors='ignore').decode('big5')


if __name__ == '__main__':

	pruned       = True
	copied_files = True
	segmented    = True

	etc_path  = 'etc'
	article_path = 'data/article'
	repo_path    = 'data/repo'
	tmp_path     = 'data/tmp'

	orig_path  = article_path+'/original_article'
	prune_path = article_path+'/prune_article'
	ws_path    = article_path+'/prune_article_ws'

	# Prune Articles
	if not pruned:

		# Compile Regex Driver
		re_url     = re.compile(r'(?:http[s]?:)?//(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
		re_script  = re.compile(r'<script(?:.|\s)*</script>')
		re_variant = ReplaceVariant()

		# Prune Articles
		for orig_file in grep_files(orig_path):
			prune_file = orig_file.replace(orig_path, prune_path)
			os.makedirs(os.path.dirname(prune_file), exist_ok=True)
			printr(prune_file)
			with open(orig_file) as fin, open(prune_file, 'w') as fout:
				fin.readline()
				lines = fin.read()
				lines = re_url.sub('', lines)
				lines = re_script.sub('', lines)
				lines = re_variant.sub(lines)
				lines = prune_string(lines+'\n')
				fout.write(lines.strip()+'\n')
		print('')


	prune_tmp_path = tmp_path+'/prune_article'
	ws_tmp_path    = tmp_path+'/prune_article_ws'

	# Copy Temp Files
	if not copied_files:

		# Remove Temp Files
		if os.path.exists(prune_tmp_path):
			shutil.rmtree(prune_tmp_path)
		if os.path.exists(ws_tmp_path):
			shutil.rmtree(ws_tmp_path)

		# Copy Files
		for prune_file in grep_files(prune_path):
			prune_tmp_file = prune_file.replace(prune_path, prune_tmp_path)
			os.makedirs(os.path.dirname(prune_tmp_file), exist_ok=True)
			printr(prune_tmp_file)
			with open(prune_file) as fin, open(prune_tmp_file, 'w', encoding='big5') as fout:
				fout.write(fin.read())
		print('')
		subprocess_call('cd {1} && rm {0}.zip && zip -q -r {0}.zip {0}/*'.format( \
				os.path.relpath(prune_tmp_path, tmp_path), tmp_path), shell=True)

	# Segment Articles
	if not segmented:

		# Word Segment
		ws = WordSegment(etc_path+'/for_article.ini', \
				[repo_path+'/core.lex', repo_path+'/brands.lex', repo_path+'/heads.lex', repo_path+'/jomalone.lex'], \
					[repo_path+'/description.lex', repo_path+'/products.lex'])

		ws(prune_tmp_path, ws_tmp_path)
		subprocess_call('unzip -q {0}.zip -d {1}'.format(ws_tmp_path, tmp_path), shell=True)
		for ws_tmp_file in grep_files(ws_tmp_path):
			ws_file = ws_tmp_file.replace(ws_tmp_path, ws_path)
			os.makedirs(os.path.dirname(ws_file), exist_ok=True)
			print(ws_file)
			ws.replace(ws_tmp_file, ws_file)
		print('')

	pass
