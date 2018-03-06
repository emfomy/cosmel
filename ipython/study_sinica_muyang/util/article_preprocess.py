#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import os
import re
import sys

sys.path.insert(0, os.path.abspath('.'))
from styleme import *


class ReplaceVariant():
	"""The driver of replacing(removing) variants in the article."""

	def __init__(self):
		pass

	def sub(self, chars):
		return chars.encode('big5', errors='ignore').decode('big5')


class SegmentPunctuation():

	__regexes = [ \
			(re.compile(r'[^\S\n]+([.,!?。，！？])'), r'\1'), \
			(re.compile(r'([.,!?。，！？])[^\S\n]+'), r'\1'), \
			(re.compile(r'([^\u4e00-\u9fff])[.。]'), r'\1'), \
			(re.compile(r'[.。]([^\u4e00-\u9fff])'), r'\1'), \
			(re.compile(r'[.]{2,}'), ''), \
			(re.compile(r'[。]{2,}'), ''), \
			(re.compile(r'[.,!?。，！？]+'), '\n')]

	def __init__(self):
		raise Exception

	@classmethod
	def sub(self, chars):
		chars = chars.lower()
		for regex in self.__regexes:
			chars = regex[0].sub(regex[1], chars)
		return chars


if __name__ == '__main__':

	assert len(sys.argv) >= 2
	ver = sys.argv[1]

	pruned         = False
	segmented      = False
	replaced_brand = False
	added_role     = False

	target       = f'pruned_article'
	etc_root     = f'etc'
	tmp_root     = f'data/tmp'
	data_root    = f'data/{ver}'
	repo_root    = f'{data_root}/repo'
	orig_root    = f'{data_root}/article/original_article'
	prune_root   = f'{data_root}/article/{target}'
	ws_orig_root = f'{data_root}/article/{target}_ws_orig'
	ws_re_root   = f'{data_root}/article/{target}_ws_re'
	ws_root      = f'{data_root}/article/{target}_ws'
	role_root    = f'{data_root}/article/{target}_role'
	parts        = ['']
	parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) >= 3: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	ckipws_lib = 'libWordSeg.so'

	# Prune Articles
	if not pruned:

		# Compile Regex Driver
		re_url     = re.compile(r'(?:http[s]?:)?//(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
		re_script  = re.compile(r'<script(?:.|\s)*</script>')
		# re_variant = ReplaceVariant()

		orig_files = grep_files(orig_root, parts=parts)
		n = str(len(orig_files))
		for i, orig_file in enumerate(orig_files):
			prune_file = transform_path(orig_file, orig_root, prune_root)
			os.makedirs(os.path.dirname(prune_file), exist_ok=True)
			printr(f'{i+1:0{len(n)}}/{n}\t{prune_file}')
			with open(orig_file) as fin, open(prune_file, 'w') as fout:
				lines = fin.read()
				lines = re_url.sub('', lines)
				lines = re_script.sub('', lines)
				# lines = re_variant.sub(lines)
				lines = SegmentPunctuation.sub(lines)
				lines = prune_string(lines+'\n')
				fout.write(lines.strip()+'\n')
		print()

	# Word-Segment Articles
	if not segmented:

		ckipws = CkipWs(ckipws_lib, etc_root+'/for_article.ini', \
				[repo_root+'/core.lex', repo_root+'/brand.lex', \
					repo_root+'/head.lex', repo_root+'/infix.lex', repo_root+'/compound.lex'], \
				[etc_root+'/compound.txt'])

		prune_files = grep_files(prune_root, parts=parts)
		n = str(len(prune_files))
		for i, prune_file in enumerate(prune_files):
			ws_orig_file = transform_path(prune_file, prune_root, ws_orig_root, '.tag')
			ws_re_file   = transform_path(prune_file, prune_root, ws_re_root, '.tag')
			os.makedirs(os.path.dirname(ws_orig_file),     exist_ok=True)
			os.makedirs(os.path.dirname(ws_re_file), exist_ok=True)
			printr(f'{i+1:0{len(n)}}/{n}\t{ws_orig_file}')
			# ckipws.ws_file(prune_file, ws_orig_file, verbose=False)
			ckipws.ws_line(prune_file, ws_orig_file, verbose=False)
			ckipws.replace(ws_orig_file, ws_re_file, verbose=False)
		print()

	# Replace Brand
	if not replaced_brand:

		repo     = Repo(repo_root)
		articles = ArticleSet(ws_re_root, parts=parts)

		n = str(len(articles))
		for i, article in enumerate(articles):

			# Replace role article to file
			for line in article:
				for m_id, txt in enumerate(line.txts):
					if txt in repo.b_name_to_brand: line.tags[m_id] = 'Nb'

			# Write article to file
			ws_file = transform_path(article.path, ws_re_root, ws_root)
			os.makedirs(os.path.dirname(ws_file), exist_ok=True)
			printr(f'{i+1:0{len(n)}}/{n}\t{ws_file}')
			with open(ws_file, 'w') as fout:
				fout.write(str(article)+'\n')

		print()

	# Add Role
	if not added_role:

		repo     = Repo(repo_root)
		articles = ArticleSet(ws_root, parts=parts)

		n = str(len(articles))
		for i, article in enumerate(articles):

			# Replace role article to file
			for line in article:
				for m_id, txt in enumerate(line.txts):
					if   txt in repo.b_name_to_brand: line.roles[m_id] = 'Brand'
					elif txt in repo.head_set:        line.roles[m_id] = 'Head'
					elif txt in repo.infix_set:       line.roles[m_id] = 'Infix'

			# Write article to file
			role_file = transform_path(article.path, ws_root, role_root, '.role')
			os.makedirs(os.path.dirname(role_file), exist_ok=True)
			printr(f'{i+1:0{len(n)}}/{n}\t{role_file}')
			with open(role_file, 'w') as fout:
				fout.write(roledstr(article)+'\n')

		print()

	pass
