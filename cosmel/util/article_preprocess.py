#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import os
import re
import sys

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *


def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Preprocesses Article.')

	argparser.add_argument('-v', '--ver', metavar='<ver>#<cver>', required=True, \
			help='load repo from "data/<ver>", and load/save corpus data from/into "data/<ver>/corpus/<cver>"')
	argparser.add_argument('-t', '--thread', metavar='<thread>', type=int, \
			help='use <thread> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	vers = args.ver.split('#')
	assert len(vers) == 2, argparser.format_usage()
	ver  = vers[0]
	cver = vers[1]
	assert len(ver)  > 0
	assert len(cver) > 0

	nth = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print(f'Use {nth} threads')

	import multiprocessing
	with multiprocessing.Pool(nth) as pool:
		results = [pool.apply_async(submain, args=(ver, cver, nth, thrank,)) for thrank in range(nth)]
		[result.get() for result in results]
		del results

	# Generate Bad-Article List
	target       = f'purged_article'
	data_root    = f'data/{ver}'
	corpus_root  = f'data/{ver}/corpus/{cver}'
	bad_article  = f'{corpus_root}/article/bad_article.txt'
	purged_root  = f'{corpus_root}/article/{target}'

	with open(bad_article, 'w') as fout:
		purged_files = glob_files(purged_root)
		n = str(len(purged_files))
		for i, purged_file in enumerate(purged_files):
			printr(f'{i+1:0{len(n)}}/{n}\t{purged_file}')
			with open(purged_file) as fin:
				for line in fin:
					if len(line) > 80:
						fout.write(Article.path_to_aid(purged_file, purged_root)+'\n')
						break
		print()


def submain(ver, cver, nth=None, thrank=0):

	purged         = False
	segmented      = False
	replaced_brand = False

	target       = f'purged_article'
	etc_root     = f'etc'
	tmp_root     = f'data/tmp'
	data_root    = f'data/{ver}'
	corpus_root  = f'data/{ver}/corpus/{cver}'
	repo_root    = f'{data_root}/repo'
	orig_root    = f'{corpus_root}/article/original_article'
	purged_root  = f'{corpus_root}/article/{target}'
	ws_re0_root  = f'{corpus_root}/article/{target}_ws_re0'
	ws_re1_root  = f'{corpus_root}/article/{target}_ws_re1'
	ws_re2_root  = f'{corpus_root}/article/{target}_ws_re2'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(orig_root))
	if nth: parts = parts[thrank:len(parts):nth]

	# Prune Articles
	if not purged:

		# Compile Regex Driver
		re_url     = re.compile(r'(?:http[s]?:)?//(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
		re_script  = re.compile(r'<script(?:.|\s)*</script>')
		# re_variant = ReplaceVariant()

		orig_files = glob_files(orig_root, parts=parts)
		n = str(len(orig_files))
		for i, orig_file in enumerate(orig_files):
			purged_file = transform_path(orig_file, orig_root, purged_root)
			os.makedirs(os.path.dirname(purged_file), exist_ok=True)
			printr(f'{i+1:0{len(n)}}/{n}\t{purged_file}')
			with open(orig_file) as fin, open(purged_file, 'w') as fout:
				lines = fin.read()
				lines = re_url.sub('', lines)
				lines = re_script.sub('', lines)
				# lines = re_variant.sub(lines)
				lines = SegmentPunctuation.sub(lines)
				lines = purge_string(lines+'\n')
				fout.write(lines.strip()+'\n')
		if not thrank: print()

	# Word-Segment Articles
	if not segmented:

		ckipws = CkipWs(etc_root+'/for_article.ini', \
				[repo_root+'/core.lex', repo_root+'/brand.lex', repo_root+'/product.lex', \
					repo_root+'/head.lex', repo_root+'/infix.lex', repo_root+'/compound.lex'], \
				[repo_root+'/compound.txt'])

		purged_files = glob_files(purged_root, parts=parts)
		n = str(len(purged_files))
		for i, purged_file in enumerate(purged_files):
			ws_re0_file = transform_path(purged_file, purged_root, ws_re0_root, '.tag')
			ws_re1_file = transform_path(purged_file, purged_root, ws_re1_root, '.tag')
			os.makedirs(os.path.dirname(ws_re0_file), exist_ok=True)
			os.makedirs(os.path.dirname(ws_re1_file), exist_ok=True)
			printr(f'{i+1:0{len(n)}}/{n}\t{ws_re0_file}')
			# ckipws.ws_file(purged_file, ws_re0_file, verbose=False)
			ckipws.ws_line(purged_file,  ws_re0_file, verbose=False)
			ckipws.replace(ws_re0_file, ws_re1_file, verbose=False)
		if not thrank: print()

	# Replace Brand
	if not replaced_brand:

		repo     = Repo(repo_root)
		articles = ArticleSet(ws_re1_root, parts=parts)

		n = str(len(articles))
		for i, article in enumerate(articles):

			# Replace role article to file
			for line in article:
				for mid, txt in enumerate(line.txts):
					if txt in repo.bname_to_brand: line.tags[mid] = 'Nb'

			# Write article to file
			ws_re2_file = transform_path(article.path, ws_re1_root, ws_re2_root)
			os.makedirs(os.path.dirname(ws_re2_file), exist_ok=True)
			printr(f'{i+1:0{len(n)}}/{n}\t{ws_re2_file}')
			article.save(ws_re2_file, str)

		if not thrank: print()


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

	main()
	print()
	pass
