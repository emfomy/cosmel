#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import os
import subprocess
import sys

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *

if __name__ == '__main__':

	assert len(sys.argv) == 2
	ver = sys.argv[1]

	data_root    = f'data/{ver}'
	parsed_root  = f'{data_root}/article/parsed_article_parse'
	tmp_root     = f'{data_root}/article/parsed_article_parse1'
	xml_root     = f'{data_root}/xml/parsed_article_ws_rid'
	parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) > 2: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	parsed_files = grep_files(parsed_root, parts=parts)
	n = str(len(parsed_files))
	for i, parsed_file in enumerate(parsed_files):
		tmp_file = transform_path(parsed_file, parsed_root, tmp_root, '.parse1')
		xml_file = transform_path(parsed_file, parsed_root, xml_root, '.xml')
		os.makedirs(os.path.dirname(tmp_file), exist_ok=True)
		os.makedirs(os.path.dirname(xml_file), exist_ok=True)
		printr(f'{i+1:0{len(n)}}/{n}\t{parsed_file}')

		subprocess.Popen(['util/rule_each.pl', ver, parsed_file, tmp_file, xml_file])
	print()

	pass
