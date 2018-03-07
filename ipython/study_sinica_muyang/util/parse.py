#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import os
import re
import sys

sys.path.insert(0, os.path.abspath('.'))
from styleme import *
from parser import CKIPParser_Client as ckipparser

def parse(line):
	uname = '_tester'
	pwd   = 'tester'
	return ckipparser.parse(line, uname, pwd, True)


if __name__ == '__main__':

	assert len(sys.argv) >= 2
	ver = sys.argv[1]

	parsed         = False

	target       = f'pruned_article'
	target_parse = f'parsed_article'
	data_root    = f'data/{ver}'
	ws_root      = f'{data_root}/article/{target}_ws'
	parsed_root  = f'{data_root}/article/{target_parse}'
	parts        = ['']
	parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) >= 3: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	ckipws_lib = 'libWordSeg.so'

	# Prune Articles
	if not parsed:
		ws_files = grep_files(ws_root, parts=parts)
		n = str(len(ws_files))
		for i, ws_file in enumerate(ws_files):
			parsed_file = transform_path(ws_file, ws_root, parsed_root, '.parse')
			os.makedirs(os.path.dirname(parsed_file), exist_ok=True)
			printr(f'{i+1:0{len(n)}}/{n}\t{parsed_file}')
			with open(ws_file) as fin, open(parsed_file, 'w') as fout:
				for ii, line in enumerate(fin):
					printr(f'{i+1:0{len(n)}}/{n}\t{parsed_file}\t{ii}')
					fout.write('\t'.join(parse(line))+'\n')
		print()

	pass
