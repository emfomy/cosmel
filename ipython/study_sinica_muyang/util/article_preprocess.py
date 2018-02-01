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
import sys

os.chdir(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.abspath('.'))
from styleme import *

class ReplaceVariant():
	"""The driver of replacing(removing) variants in the article."""

	def __init__(self):
		pass

	def sub(self, chars):
		return chars.encode('big5', errors='ignore').decode('big5')


if __name__ == '__main__':

	pruned           = True
	copied_files     = True
	segmented        = True
	replaced_product = True

	etc_root  = 'etc'
	article_root = 'data/article'
	repo_root    = 'data/repo'
	tmp_root     = 'data/tmp'

	orig_root  = article_root+'/original_article'
	prune_root = article_root+'/prune_article'
	ws_root    = article_root+'/prune_article_ws'

	prune_tmp_root = tmp_root+'/prune_article'
	ws_tmp_root    = tmp_root+'/prune_article_ws'
	ws_re_tmp_root = tmp_root+'/prune_article_ws_re'

	# Prune Articles
	if not pruned:

		# Compile Regex Driver
		re_url     = re.compile(r'(?:http[s]?:)?//(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
		re_script  = re.compile(r'<script(?:.|\s)*</script>')
		re_variant = ReplaceVariant()

		for orig_file in grep_files(orig_root):
			prune_file = orig_file.replace(orig_root, prune_root)
			os.makedirs(os.path.dirname(prune_file), exist_ok=True)
			print(prune_file)
			with open(orig_file) as fin, open(prune_file, 'w') as fout:
				fin.readline()
				lines = fin.read()
				lines = re_url.sub('', lines)
				lines = re_script.sub('', lines)
				lines = re_variant.sub(lines)
				lines = prune_string(lines+'\n')
				fout.write(lines.strip()+'\n')
		print()

	# Copy Temp Files
	if not copied_files:

		# Remove Temp Files
		if os.path.exists(prune_tmp_root):
			shutil.rmtree(prune_tmp_root)
		if os.path.exists(ws_tmp_root):
			shutil.rmtree(ws_tmp_root)
		if os.path.exists(ws_re_tmp_root):
			shutil.rmtree(ws_re_tmp_root)

		# Copy Files
		for prune_file in grep_files(prune_root):
			prune_tmp_file = prune_file.replace(prune_root, prune_tmp_root)
			os.makedirs(os.path.dirname(prune_tmp_file), exist_ok=True)
			print(prune_tmp_file)
			with open(prune_file) as fin, open(prune_tmp_file, 'w', encoding='big5') as fout:
				fout.write(fin.read())
		print()

		rel_tmp_root = os.path.relpath(prune_tmp_root, tmp_root)
		subprocess_call(f'cd {tmp_root} && rm {rel_tmp_root}.zip && zip -q -r {rel_tmp_root}.zip {rel_tmp_root}/*', shell=True)

	# Segment Articles
	if not segmented:

		# Word Segment
		ws = WordSegment(etc_root+'/for_article.ini', \
				[repo_root+'/core.lex', repo_root+'/brands.lex', repo_root+'/heads.lex', repo_root+'/jomalone.lex'], \
					[repo_root+'/infix.lex', repo_root+'/products.lex'])

		ws(prune_tmp_root, ws_tmp_root)
		subprocess_call(f'unzip -q {ws_tmp_root}.zip -d {tmp_root}', shell=True)

		# Replace post-tags
		for ws_tmp_file in grep_files(ws_tmp_root):
			ws_re_tmp_file = ws_tmp_file.replace(ws_tmp_root, ws_re_tmp_root)
			os.makedirs(os.path.dirname(ws_re_tmp_file), exist_ok=True)
			print(ws_re_tmp_file)
			ws.replace(ws_tmp_file, ws_re_tmp_file)
		print()

	if not replaced_product:

		tag_dict = {}
		with open(repo_root+'/products.lex') as fin_lex, open(repo_root+'/products.tag') as fin_tag:
			for line_lex, line_tag in zip(fin_lex, fin_tag):
				line_lex = line_lex.strip()
				line_tag = line_tag.strip()
				assert not line_lex == ''
				assert not line_tag == ''
				tag_dict[line_lex.split('\t')[0]] = line_tag

		regexes = []
		for lex, tag in tag_dict.items():
			regexes.append((re.compile(rf'(\A|(?<=\n|　)){lex}\(N_Product\)'), tag, lex))

		# Replace N_Product
		for ws_re_tmp_file in grep_files(ws_re_tmp_root):
			ws_file = ws_re_tmp_file.replace(ws_re_tmp_root, ws_root)
			os.makedirs(os.path.dirname(ws_file), exist_ok=True)
			print(ws_file)
			with open(ws_re_tmp_file) as fin, open(ws_file, 'w') as fout:
				lines = fin.read()
				for regex in regexes:
					printr(regex[2])
					lines = regex[0].sub(regex[1], lines)
				fout.write(lines)
		print()

	pass
