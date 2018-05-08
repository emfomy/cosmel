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

	target       = f'pruned_article'
	tmp_root     = f'data/tmp'
	data_root    = f'data/{ver}'
	base_root    = f'{data_root}/mention/{target}_gid_20180420'
	input_root   = '/home/emfomy/corpus/pixnet/raw/20180502/json'
	output_root  = f'{data_root}/mention/{target}_gid_20180502'
	parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
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
					# data.pop('sid', None)
					# data.pop('mid', None)

					# data.pop('hint', None)
					# data.pop('hint_orio', None)

					if 'gid' not in data or not data['gid']:
						print(colored('1;33', f'[No GID] Remove {input_file}:{key[0]}:{key[1]}'))
						continue
					data = {'gid': data['gid']}

					data = dict((attr, value,) for attr, value in data.items() if value)

					if key in data_dict:
						data_dict[key].update(data)
					else:
						print(colored('1;31', f'Unknown mention {input_file}:{key[0]}:{key[1]}!'))
		except Exception as e:
			print()
			print(colored('0;33', e))
			pass

		with open(output_file, 'w') as fout:
			for data in data_dict.values():
				fout.write(json.dumps(data)+'\n')

	print()

	pass
