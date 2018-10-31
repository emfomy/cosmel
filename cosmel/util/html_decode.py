#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import os
import sys

from bs4 import BeautifulSoup

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *


def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Decode HTML.')

	argparser.add_argument('-c', '--corpus', required=True,
			help='store corpus data in directory "<CORPUS>/"')

	argparser.add_argument('-i', '--input', required=True, \
			help='load HTML from "<CORPUS>/html/<INPUT>/"')
	argparser.add_argument('-o', '--output', \
			help='dump mention into "data/<ver>/mention/<OUTPUT>/"; default is <INPUT>')

	argparser.add_argument('-t', '--thread', type=int, \
			help='use <THREAD> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	corpus_root = os.path.normpath(args.corpus)

	in_dir    = args.input
	out_dir   = args.output
	if not out_dir:
		out_dir = in_dir

	nth = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print(f'Use {nth} threads')

	if nth <= 1:
		submain(corpus_root, in_dir, out_dir)
	else:
		import multiprocessing
		jobs = [multiprocessing.Process(target=submain, args=(corpus_root, in_dir, out_dir, nth, thrank,)) for thrank in range(nth)]
		for p in jobs: p.start()
		for p in jobs: p.join()
		for p in jobs: assert p.exitcode == 0


def submain(corpus_root, in_dir, out_dir, nth=None, thrank=0):

	target       = f'purged_article'
	html_root    = f'{corpus_root}/html/{in_dir}'
	article_root = f'{corpus_root}/article/{target}_role'
	mention_root = f'{corpus_root}/mention/{target}'
	output_root  = f'{corpus_root}/mention/{out_dir}'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(html_root))
	if nth: parts = parts[thrank:len(parts):nth]

	# Load CosmEL repository and corpus
	corpus = Corpus(article_root, mention_root=mention_root, parts=parts)

	# Extract html from json
	n = str(len(corpus.article_set))
	for i, article in enumerate(corpus.article_set):
		html_file   = transform_path(article.path, article_root, html_root, '.xml.html')
		output_file = transform_path(article.path, article_root, output_root, '.json')
		os.makedirs(os.path.dirname(output_file), exist_ok=True)
		bundle      = article.bundle
		printr(f'{i+1:0{len(n)}}/{n}\t{output_file}')

		try:
			fin = open(html_file)
		except FileNotFoundError as e:
			printr(colored('0;33', e))
		except Exception as e:
			print()
			print(colored('1;31', e))
		else:
			soup = BeautifulSoup(fin.read(), 'lxml')
			for product in soup.find_all('product'):
				attrs = product.attrs
				try:
					sid = int(attrs['sid'])
					mid = int(attrs['mid'])
					mention = corpus.id_to_mention[article.aid, sid, mid]
				except KeyError as e:
					print(colored('1;31', f'Skip unknown mention in {html_file}: {product}'))
					print()
				except Exception as e:
					print()
					print(colored('1;31', e))
				else:
					mention.set_gid(attrs.pop('pid', mention.gid))
					mention.set_gid(attrs.pop('gid', mention.gid))
					mention.set_nid(attrs.pop('nid', mention.nid))
					mention.set_rid(attrs.pop('rid', mention.rid))
					mention.set_rule(attrs.pop('rule', mention.rule))

			fin.close()

		bundle.save(output_file)
	if not thrank: print()


if __name__ == '__main__':

	main()
	print()
	pass
