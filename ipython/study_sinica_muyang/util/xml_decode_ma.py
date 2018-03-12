#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import os
import sys

os.chdir(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.abspath('.'))
from styleme import *

def grep_mention(article, sid, mid, txt):
	pid  = txt.split('pid="')[1].split('"')[0]
	gid  = txt.split('gid="')[1].split('"')[0]
	rule = txt.split('rule="')[1].split('"')[0]
	return Mention(article, sid, mid, pid=pid, gid=gid, rule=rule)

if __name__ == '__main__':

	assert len(sys.argv) >= 2
	ver = sys.argv[1]

	get_mention = False
	get_article = False

	target        = f'pruned_article_ma'
	target_ver    = f''
	target_ver    = f'_pid'
	# target_ver   = f'_exact'
	tmp_root      = f'data/tmp'
	data_root     = f'data/{ver}'
	repo_root     = f'{data_root}/repo'
	xml_root      = f'{data_root}/xml/{target}{target_ver}'
	article_root  = f'{data_root}/article/{target}_role'
	mention_root  = f'{data_root}/mention/{target}{target_ver}'
	parts         = ['']
	parts         = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) >= 3: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	empty_file = tmp_root+'/empty.tmp'
	with open(empty_file, 'w'): pass

	repo = Repo(repo_root)
	xmls = ArticleSet(xml_root, parts=parts)

	if not get_mention:
		for xml in xmls:
			mention_file = transform_path(xml.path.replace('.label', ''), xml_root, mention_root, '.json')
			bundle = MentionBundle(empty_file, xml)
			bundle._MentionBundle__data = [grep_mention(xml, sid, mid, txt) \
					for sid, line in enumerate(xml) for mid, txt in enumerate(line.txts) if '<' in txt]
			bundle.save(mention_file)
		print()

	if not get_article:
		n = str(len(xmls))
		for i, xml in enumerate(xmls):

			# Replace role xml to file
			for line in xml:
				for mid, txt in enumerate(line.txts):
					if '<' in txt:
						line.txts[mid] = txt.split('>')[1]
						line.roles[mid] = ''
					if   txt in repo.bname_to_brand:        line.roles[mid] = 'Brand'
					elif txt in repo.head_set:              line.roles[mid] = 'Head'
					elif txt in repo.infix_set:             line.roles[mid] = 'Infix'
					elif txt in repo.pname_to_product_list: line.roles[mid] = 'PName'

			# Write xml to file
			article_file = transform_path(xml.path.replace('.label', ''), xml_root, article_root, '.role')
			os.makedirs(os.path.dirname(article_file), exist_ok=True)
			printr(f'{i+1:0{len(n)}}/{n}\t{article_file}')
			with open(article_file, 'w') as fout:
				fout.write(roledstr(xml)+'\n')
		print()

	pass
