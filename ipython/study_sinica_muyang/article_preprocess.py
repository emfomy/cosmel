#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import functools
import multiprocessing
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

	num_pool = 8

	pruned           = True
	copied_files     = True
	segmented        = True
	replaced_product = True

	etc_path  = 'etc'
	article_path = 'data/article'
	repo_path    = 'data/repo'
	tmp_path     = 'data/tmp'

	orig_path  = article_path+'/original_article'
	prune_path = article_path+'/prune_article'
	ws_path    = article_path+'/prune_article_ws'

	prune_tmp_path = tmp_path+'/prune_article'
	ws_tmp_path    = tmp_path+'/prune_article_ws'
	ws_re_tmp_path = tmp_path+'/prune_article_ws_re'

	# Prune Articles
	if not pruned:

		# Compile Regex Driver
		re_url     = re.compile(r'(?:http[s]?:)?//(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
		re_script  = re.compile(r'<script(?:.|\s)*</script>')
		re_variant = ReplaceVariant()

		def func(re_url, re_script, re_variant, orig_path, prune_path, orig_file):
			prune_file = orig_file.replace(orig_path, prune_path)
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

		with multiprocessing.Pool(num_pool) as p:
			p.map(functools.partial(func, re_url, re_script, re_variant, orig_path, prune_path), grep_files(orig_path))
		print('')

	# Copy Temp Files
	if not copied_files:

		# Remove Temp Files
		if os.path.exists(prune_tmp_path):
			shutil.rmtree(prune_tmp_path)
		if os.path.exists(ws_tmp_path):
			shutil.rmtree(ws_tmp_path)
		if os.path.exists(ws_re_tmp_path):
			shutil.rmtree(ws_re_tmp_path)

		# Copy Files
		def func(prune_path, prune_tmp_path, prune_file):
			prune_tmp_file = prune_file.replace(prune_path, prune_tmp_path)
			os.makedirs(os.path.dirname(prune_tmp_file), exist_ok=True)
			print(prune_tmp_file)
			with open(prune_file) as fin, open(prune_tmp_file, 'w', encoding='big5') as fout:
				fout.write(fin.read())

		with multiprocessing.Pool(num_pool) as p:
			p.map(functools.partial(func, prune_path, prune_tmp_path, prune_file), grep_files(prune_path))
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

		# Replace post-tags
		def func(ws, ws_tmp_path, ws_re_tmp_path, ws_tmp_file):
			ws_re_tmp_file = ws_tmp_file.replace(ws_tmp_path, ws_re_tmp_path)
			os.makedirs(os.path.dirname(ws_re_tmp_file), exist_ok=True)
			print(ws_re_tmp_file)
			ws.replace(ws_tmp_file, ws_re_tmp_file)

		with multiprocessing.Pool(num_pool) as p:
			p.map(functools.partial(func, ws, ws_tmp_path, ws_re_tmp_path), grep_files(ws_tmp_path))
		print('')

	if not replaced_product:

		tag_dict = {}
		with open(repo_path+'/products.lex') as fin_lex, open(repo_path+'/products.tag') as fin_tag:
			for line_lex, line_tag in zip(fin_lex, fin_tag):
				line_lex = line_lex.strip()
				line_tag = line_tag.strip()
				assert not line_lex == ''
				assert not line_tag == ''
				tag_dict[line_lex.split('\t')[0]] = line_tag

		regexes = []
		for lex, tag in tag_dict.items():
			regexes.append((re.compile(r'(\A|(?<=\n|　)){}\(N_Product\)'.format(lex)), tag, lex))

		# Replace N_Product
		def func(regexes, ws_path, ws_re_tmp_path, ws_file):
			ws_file = ws_re_tmp_file.replace(ws_re_tmp_path, ws_path)
			os.makedirs(os.path.dirname(ws_file), exist_ok=True)
			print(ws_file)
			with open(ws_re_tmp_file) as fin, open(ws_file, 'w') as fout:
				lines = fin.read()
				for regex in regexes:
					print(regex[2])
					lines = regex[0].sub(regex[1], lines)
				fout.write(lines)

		with multiprocessing.Pool(num_pool) as p:
			p.map(functools.partial(func, regexes, ws_path, ws_re_tmp_path), grep_files(ws_re_tmp_path))
		print('')

	pass
