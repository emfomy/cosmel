#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import os
import sys

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *


def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Merge Mention.')

	argparser.add_argument('-v', '--ver', metavar='<ver>#<cver>', required=True, \
			help='load repo from "data/<ver>", and load/save corpus data from/into "data/<ver>/corpus/<cver>"')

	argparser.add_argument('-b', '--base', metavar='<base_dir>', required=True, \
			help='load mention from "data/<ver>/corpus/<cver>/mention/<base_dir>"')
	argparser.add_argument('-i', '--input', metavar='<in_dir>', required=True, \
			help='load mention from "data/<ver>/corpus/<cver>/mention/<in_dir>"')
	argparser.add_argument('-o', '--output', metavar='<out_dir>', required=True, \
			help='dump XML into "data/<ver>/html/<out_dir>"; default is <in_dir>')

	argparser.add_argument('-t', '--thread', metavar='<thread>', type=int, \
			help='use <thread> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	vers = args.ver.split('#')
	assert len(vers) == 2, argparser.format_usage()
	ver  = vers[0]
	cver = vers[1]
	assert len(ver)  > 0
	assert len(cver) > 0

	base_dir = args.base
	in_dir   = args.input
	out_dir  = args.output

	nth      = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print(f'Use {nth} threads')

	import multiprocessing
	with multiprocessing.Pool(nth) as pool:
		results = [pool.apply_async(submain, args=(ver, cver, base_dir, in_dir, out_dir, nth, thrank,)) for thrank in range(nth)]
		[result.get() for result in results]
		del results


def submain(ver, cver, base_dir, in_dir, out_dir, nth=None, thrank=0):

	target       = f'purged_article'
	tmp_root     = f'data/tmp'
	data_root    = f'data/{ver}'
	corpus_root  = f'data/{ver}/corpus/{cver}'
	base_root    = f'{corpus_root}/mention/{base_dir}'
	input_root   = f'{corpus_root}/mention/{in_dir}'
	output_root  = f'{corpus_root}/mention/{out_dir}'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(base_root))
	if nth: parts = parts[thrank:len(parts):nth]

	# Embed input mention
	base_files = glob_files(base_root, parts)
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
					data.pop('sid', None)
					data.pop('mid', None)

					# if 'gid' not in data or not data['gid']:
					# 	print(colored('1;33', f'[No GID] Remove {input_file}:{key[0]}:{key[1]}'))
					# 	continue

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

	if not thrank: print()


if __name__ == '__main__':

	main()
	print()
	pass
