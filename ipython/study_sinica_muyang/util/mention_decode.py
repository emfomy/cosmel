#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import os
import sys

sys.path.insert(0, os.path.abspath('.'))
from styleme import *


if __name__ == '__main__':

	assert len(sys.argv) >= 2
	ver = sys.argv[1]

	greped_mention   = False
	written_sentence = True

	target       = f'parsed_article'
	target_ver   = f''
	target_ver   = f'_ckip_gid'
	tmp_root     = f'data/tmp'
	data_root    = f'data/{ver}'
	input_root   = f'host/{ver}/json'
	output_root  = f'{data_root}/mention/{target}{target_ver}'
	parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) >= 3: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	# Remove duplicated mentions
	input_files = grep_files(input_root, parts)
	n = str(len(input_files))
	for i, input_file in enumerate(input_files):
		output_file = transform_path(input_file, input_root, output_root)
		os.makedirs(os.path.dirname(output_file), exist_ok=True)
		printr(f'{i+1:0{len(n)}}/{n}\t{output_file}')

		with open(input_file) as fin, open(output_file, 'w') as fout:
			data_dict = dict()
			for line in fin:
				data = json.loads(line)
				data_dict[(data['sid'], data['mid'],)] = data

			for data in data_dict.values():
				fout.write(json.dumps(data)+'\n')
	print()

	pass
