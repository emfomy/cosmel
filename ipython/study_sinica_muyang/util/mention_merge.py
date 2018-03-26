#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import os
import sys

sys.path.insert(0, os.path.abspath('.'))
from styleme import *


if __name__ == '__main__':

	assert len(sys.argv) > 1
	ver = sys.argv[1]

	greped_mention   = False
	written_sentence = True

	target       = f'pruned_article'
	target_ver   = f''
	target_ver   = f'_gid'
	# target_ver   = f'_gid_orio'
	tmp_root     = f'data/tmp'
	data_root    = f'data/{ver}'
	input_root   = f'host/{ver}/json'
	# input_root   = f'host/{ver}/mention'
	base_root    = f'{data_root}/mention/{target}'
	base_root    = f'{data_root}/mention/{target}_gid_orio'
	output_root  = f'{data_root}/mention/{target}{target_ver}'
	parts        = ['']
	parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) > 2: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	# Embed input mention
	base_files = grep_files(base_root, parts)
	n = str(len(base_files))
	for i, base_file in enumerate(base_files):
		input_file  = transform_path(base_file, base_root, input_root)
		output_file = transform_path(base_file, base_root, output_root)
		os.makedirs(os.path.dirname(output_file), exist_ok=True)
		printr(f'{i+1:0{len(n)}}/{n}\t{output_file}')

		data_dict = dict()
		with open(base_file) as fin:
			for line in fin:
				data = json.loads(line)
				data_dict[(int(data['sid']), int(data['mid']),)] = data

		try:
			with open(input_file) as fin:
				for line in fin:
					data = json.loads(line)
					key = (int(data['sid']), int(data['mid']),)
					del data['sid']
					del data['mid']

					del data['hint']
					del data['hint_orio']

					data = dict((attr, value,) for attr, value in data.items() if value)

					if key in data_dict:
						data_dict[key].update(data)
					else:
						print(colored('1;31', f'\nUnknown mention {input_file}:{key[0]}:{key[1]}!\n'))
		except Exception as e:
			print()
			print(colored('0;33', e))

		with open(output_file, 'w') as fout:
			for data in data_dict.values():
				fout.write(json.dumps(data)+'\n')

	print()

	pass
