#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import itertools
import os
import re
import sys

from bs4 import BeautifulSoup

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *

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

	assert len(sys.argv) > 1
	ver = sys.argv[1]

	textualized = False
	get_mention = False

	target        = f'pruned_article'
	target2       = f'parsed_article'
	target_ver    = f''
	target_ver    = f'_rid'
	tmp_root      = f'data/tmp'
	data_root     = f'data/{ver}'
	repo_root     = f'{data_root}/repo'
	ws_xml_root   = f'{data_root}/xml/{target2}_ws{target_ver}'
	xml_root      = f'{data_root}/xml/{target2}{target_ver}'
	article_root  = f'{data_root}/article/{target}_role'
	mention_root  = f'{data_root}/mention/{target}{target_ver}'
	parts         = ['']
	# parts         = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) > 2: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

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
		print()

	# Grep mention
	if not get_mention:

		def repl(m): return '□' * len(m.group())
		regex = re.compile('<[^<>]*?>')

		xml_files = grep_files(xml_root, parts)
		n = str(len(xml_files))
		for i, xml_file in enumerate(xml_files):
			article_file = transform_path(xml_file, xml_root, article_root, '.role')
			mention_file = transform_path(xml_file, xml_root, mention_root, '.json')
			article = Article(article_file)
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
		print()

	pass
