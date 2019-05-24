#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import argparse
import itertools
import os
import re
import sys

from bs4 import BeautifulSoup

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *


def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Decode XML.')

	argparser.add_argument('-c', '--corpus', required=True,
			help='store corpus data in directory "<CORPUS>/"')

	argparser.add_argument('-iw', '--input-ws', \
			help='load word-segmented XML from "<CORPUS>/xml/<INPUT-WS>/"')
	argparser.add_argument('-i', '--input', required=True, \
			help='load XML from "<CORPUS>/xml/<INPUT>/"')
	argparser.add_argument('-o', '--output', \
			help='dump mention into "data/<ver>/mention/<OUTPUT>/"; default is <INPUT>')

	argparser.add_argument('-t', '--thread', type=int, \
			help='use <THREAD> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	corpus_root = os.path.normpath(args.corpus)

	in_ws_dir = args.input_ws
	in_dir    = args.input
	out_dir   = args.output
	if not out_dir:
		out_dir = in_dir

	nth     = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print(f'Use {nth} threads')

	if nth <= 1:
		submain(corpus_root, in_ws_dir, in_dir, out_dir)
	else:
		import multiprocessing
		jobs = [multiprocessing.Process(target=submain, args=(corpus_root, in_ws_dir, in_dir, out_dir, nth, thrank,)) \
				for thrank in range(nth)]
		for p in jobs: p.start()
		for p in jobs: p.join()
		for p in jobs: assert p.exitcode == 0


def submain(corpus_root, in_ws_dir, in_dir, out_dir, nth=None, thrank=0):

	textualized = (in_ws_dir == None)
	get_mention = False

	target       = f'purged_article'
	ws_xml_root  = f'{corpus_root}/xml/{in_ws_dir}'
	xml_root     = f'{corpus_root}/xml/{in_dir}'
	article_root = f'{corpus_root}/article/{target}_role'
	mention_root = f'{corpus_root}/mention/{target}'
	output_root  = f'{corpus_root}/mention/{out_dir}'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	if in_ws_dir: parts = sorted(rm_ext_all(file) for file in os.listdir(ws_xml_root))
	else:         parts = sorted(rm_ext_all(file) for file in os.listdir(xml_root))
	if nth: parts = parts[thrank:len(parts):nth]

	# Textualize
	if not textualized:
		ws_xmls = ArticleSet(ws_xml_root, parts=parts)
		n = str(len(ws_xmls))
		for i, ws_xml in enumerate(ws_xmls):
			xml_file = transform_path(ws_xml.path, ws_xml_root, xml_root, '.xml')
			os.makedirs(os.path.dirname(xml_file), exist_ok=True)
			printr(f'{i+1:0{len(n)}}/{n}\t{xml_file}')
			ws_xml.save(xml_file, roledtxtstr)
		if not thrank: print()

	# Grep mention
	if not get_mention:

		corpus = Corpus(article_root, mention_root=mention_root, parts=parts)

		def repl(m): return '□' * len(m.group())
		regex = re.compile('<[^<>]*?>')

		n = str(len(corpus.article_set))
		for i, article in enumerate(corpus.article_set):
			xml_file    = transform_path(article.path, article_root, xml_root, '.xml')
			output_file = transform_path(article.path, article_root, output_root, '.json')
			os.makedirs(os.path.dirname(output_file), exist_ok=True)
			bundle      = article.bundle
			printr(f'{i+1:0{len(n)}}/{n}\t{output_file}')

			try:
				fin = open(xml_file)
			except FileNotFoundError as e:
				printr(colored('0;33', e))
			except Exception as e:
				print()
				print(colored('1;31', e))
			else:
				for sid, (line, xml_line) in enumerate(zip(article, fin)):

					xml_line = xml_line.strip()
					xml_line_re = regex.sub(repl, xml_line)

					# Map Index
					xml_idx = -1
					txt_list = ['*'] * len(xml_line)
					start_mid_list = [len(line)-1] * len(xml_line)
					end_mid_list   = [-1] * len(xml_line)
					for mid, word in enumerate(line.txts):
						chars = ''.join(word.replace('□', ''))
						for char in chars:
							try:
								xml_idx0 = xml_idx
								xml_idx  = get_xml_idx(xml_line_re, char, xml_idx0)
							except ValueError:
								pass
							else:
								txt_list[xml_idx] = char
								for idx in range(xml_idx0+1, xml_idx+1):  start_mid_list[idx] = mid
								for idx in range(xml_idx, len(xml_line)): end_mid_list[idx]   = mid

					# Extract XML Tag
					end_idx = 0
					while '<product ' in xml_line[(end_idx+1):]:
						start_idx = get_xml_idx(xml_line, '<product ', end_idx)
						end_idx   = get_xml_idx(xml_line, '</product', start_idx)
						start_mid = start_mid_list[start_idx]
						end_mid   = end_mid_list[end_idx]

						if start_mid != end_mid:
							print(colored('1;31', f'Skip wrong mention at {xml_file}:{sid}:{start_idx}-{end_idx}'))
							print(f'{xml_line[:start_idx]}{colored("0;95", xml_line[start_idx:end_idx])}{xml_line[end_idx:]}')
							print(f'{line[:start_mid]}　[{colored("0;95", line[start_mid:end_mid+1])}]　{line[end_mid+1:]}')
							print()
						else:
							try:
								mention = corpus.id_to_mention[article.aid, sid, start_mid]
							except KeyError as e:
								print(colored('1;31', f'Skip unknown mention at {xml_file}:{sid}:{start_idx}-{end_idx}'))
								print(f'{xml_line[:start_idx]}{colored("0;95", xml_line[start_idx:end_idx])}{xml_line[end_idx:]}')
								print(f'{line[:start_mid]}　[{colored("0;95", line[start_mid:end_mid+1])}]　{line[end_mid+1:]}')
								print()
							except Exception as e:
								print()
								print(colored('1;31', e))
							else:
								update_mention(mention, xml_line[start_idx:end_idx+1])
				fin.close()

			bundle.save(output_file)
		if not thrank: print()


def get_xml_idx(xml_data, word, start_idx):
	return xml_data[(start_idx+1):].index(word)+(start_idx+1)


def update_mention(mention, txt):
	soup = BeautifulSoup(txt.split('>', 1)[0]+'>', 'lxml')
	attrs = soup.product.attrs
	mention.set_gid(attrs.pop('pid', mention.gid))
	mention.set_gid(attrs.pop('gid', mention.gid))
	mention.set_nid(attrs.pop('nid', mention.nid))
	mention.set_rid(attrs.pop('rid', mention.rid))
	mention.set_rule(attrs.pop('rule', mention.rule))


if __name__ == '__main__':

	main()
	print()
	pass
