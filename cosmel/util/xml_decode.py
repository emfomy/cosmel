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

	argparser.add_argument('-v', '--ver', metavar='<ver>#<date>', required=True, \
			help='load repo from "data/<ver>", and load/save corpus data from/into "data/<ver>/corpus/<date>"')

	argparser.add_argument('-iw', '--input_ws', metavar='<in_ws_dir>', \
			help='load word-segmented XML from "data/<ver>/xml/<in_ws_dir>"')
	argparser.add_argument('-i', '--input', metavar='<in_dir>', required=True, \
			help='load XML from "data/<ver>/xml/<in_dir>"')
	argparser.add_argument('-o', '--output', metavar='<out_dir>', \
			help='dump mention into "data/<ver>/mention/<out_dir>"; default is <in_dir>')

	argparser.add_argument('-t', '--thread', metavar='<thread>', type=int, \
			help='use <thread> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	vers = args.ver.split('#')
	assert len(vers) == 2, argparser.format_usage()
	ver  = vers[0]
	date = vers[1]
	assert len(ver)  > 0
	assert len(date) > 0

	in_ws_dir = args.input_ws
	in_dir    = args.input
	out_dir   = args.output
	if not out_dir:
		out_dir = in_dir

	nth     = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print(f'Use {nth} threads')

	import multiprocessing
	with multiprocessing.Pool(nth) as pool:
		results = [pool.apply_async(submain, args=(ver, date, in_ws_dir, in_dir, out_dir, nth, thrank,)) for thrank in range(nth)]
		[result.get() for result in results]
		del results


def submain(ver, date, in_ws_dir, in_dir, out_dir, nth=None, thrank=0):

	textualized = (in_ws_dir == None)
	get_mention = False

	target       = f'purged_article'
	tmp_root     = f'data/tmp'
	data_root    = f'data/{ver}'
	corpus_root  = f'data/{ver}/corpus/{date}'
	repo_root    = f'{data_root}/repo'
	ws_xml_root  = f'{corpus_root}/xml/{in_ws_dir}'
	xml_root     = f'{corpus_root}/xml/{in_dir}'
	article_root = f'{corpus_root}/article/{target}_role'
	mention_root = f'{corpus_root}/mention/{out_dir}'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	if in_ws_dir: parts = sorted(rm_ext_all(file) for file in os.listdir(ws_xml_root))
	else:         parts = sorted(rm_ext_all(file) for file in os.listdir(xml_root))
	if nth: parts = parts[thrank:len(parts):nth]

	empty_file = tmp_root+'/empty.tmp'
	with open(empty_file, 'w'): pass

	repo = Repo(repo_root)

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

		def repl(m): return '□' * len(m.group())
		regex = re.compile('<[^<>]*?>')

		xml_files = glob_files(xml_root, parts)
		n = str(len(xml_files))
		for i, xml_file in enumerate(xml_files):
			article_file = transform_path(xml_file, xml_root, article_root, '.role')
			mention_file = transform_path(xml_file, xml_root, mention_root, '.json')
			article = Article(article_file, article_root)
			bundle = MentionBundle(empty_file, article)
			printr(f'{i+1:0{len(n)}}/{n}\t{mention_file}')

			with open(xml_file) as fin:
				for sid, (line, xml_line) in enumerate(zip(article, fin)):

					xml_line = xml_line.strip()
					xml_line_re = regex.sub(repl, xml_line)

					# Map Index
					xml_idx = -1
					txt_list = ['*']  * len(xml_line)
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

					# Grep XML Tag
					end_idx = 0
					while '<product ' in xml_line[(end_idx+1):]:
						start_idx = get_xml_idx(xml_line, '<product ', end_idx)
						end_idx   = get_xml_idx(xml_line, '</product', start_idx)
						start_mid = start_mid_list[start_idx]
						end_mid   = end_mid_list[end_idx]

						if start_mid != end_mid or line.roles[start_mid] != 'Head':
							print(colored('1;31', f'Skip mention at {xml_file}:{sid}:{start_idx}-{end_idx}'))
							print(f'{xml_line[:start_idx]}{colored("0;95", xml_line[start_idx:end_idx])}{xml_line[end_idx:]}')
							print(f'{line[:start_mid]}　[{colored("0;95", line[start_mid:end_mid+1])}]　{line[end_mid+1:]}')
							print()
							continue

						bundle._MentionBundle__data.append(grep_mention(article, sid, start_mid, xml_line[start_idx:end_idx+1]))

			bundle.save(mention_file)
		if not thrank: print()


def get_xml_idx(xml_data, word, start_idx):
	return xml_data[(start_idx+1):].index(word)+(start_idx+1)


def grep_mention(article, sid, mid, txt):
	soup = BeautifulSoup(txt.split('>', 1)[0]+'>', 'lxml')
	attrs = soup.product.attrs
	attrs.pop('sid', None)
	attrs.pop('mid', None)
	attrs = dict((attr, value,) for attr, value in attrs.items() if value)

	return Mention(article, sid, mid, **attrs)


if __name__ == '__main__':

	main()
	print()
	pass
