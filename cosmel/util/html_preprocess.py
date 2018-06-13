#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import html
import json
import os
import re
import sys

from bs4 import BeautifulSoup

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *

def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Preprocesses HTML.')

	argparser.add_argument('-c', '--corpus', required=True,
		help='store corpus data in directory "<CORPUS>/"')
	argparser.add_argument('-t', '--thread', type=int, \
			help='use <THREAD> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	corpus_root = os.path.normpath(args.corpus)

	nth = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print(f'Use {nth} threads')

	import multiprocessing
	with multiprocessing.Pool(nth) as pool:
		results = [pool.apply_async(submain, args=(corpus_root, nth, thrank,)) for thrank in range(nth)]
		[result.get() for result in results]
		del results


def submain(corpus_root, nth=None, thrank=0):

	replaced  = False
	parsed    = False

	etc_root     = f'etc'
	html_root    = f'{corpus_root}/html/html_article'
	article_root = f'{corpus_root}/article/original_article'
	notag_root   = f'{corpus_root}/html/html_article_notag'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(html_root))
	if nth: parts = parts[thrank:len(parts):nth]

	# Replace html tags
	if not replaced:
		def repl(m): return '□' * len(m.group())
		regex_tag = re.compile('<[^<>]*?>')
		regex_url  = re.compile(r'(?:http[s]?:)?//(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
		for html_file in glob_files(html_root, parts):
			notag_file = html_file.replace(html_root, notag_root)
			os.makedirs(os.path.dirname(notag_file), exist_ok=True)
			printr(notag_file)
			with open(html_file) as fin, open(notag_file, 'w') as fout:
				data = fin.read().lower()
				data = regex_tag.sub(repl, data)
				data = regex_url.sub(repl, data)
				fout.write(data)
		if not thrank: print()

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

		for html_file in glob_files(html_root, parts):
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
		if not thrank: print()

from cosmel import *

def get_html_idx(html_data, html_idx, word):
	try:
		return html_data[html_idx:].index(word)+html_idx
	except ValueError:
		return html_idx

if __name__ == '__main__':

	main()
	print()
	pass
