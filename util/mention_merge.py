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

	argparser.add_argument('-c', '--corpus', required=True,
			help='store corpus data in directory "<CORPUS>/"')

	argparser.add_argument('-b', '--base', required=True, \
			help='load mention from "<CORPUS>/mention/<BASE>/"')
	argparser.add_argument('-i', '--input', required=True, \
			help='load mention from "<CORPUS>/mention/<INPUT>/"')
	argparser.add_argument('-o', '--output', required=True, \
			help='dump XML into "data/<ver>/html/<OUTPUT>/"; default is <INPUT>')

	argparser.add_argument('-f', '--flag', choices=['gid', 'nid', 'rid'], nargs='*', default=[], \
			help='copy <FLAG> only; default is "[]" (all)')

	argparser.add_argument('-t', '--thread', type=int, \
			help='use <THREAD> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	corpus_root = os.path.normpath(args.corpus)

	base_dir = args.base
	in_dir   = args.input
	out_dir  = args.output

	flags    = set(args.flag)

	nth      = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print(f'Use {nth} threads')

	if nth <= 1:
		submain(corpus_root, base_dir, in_dir, out_dir)
	else:
		import multiprocessing
		jobs = [multiprocessing.Process(target=submain, args=(corpus_root, base_dir, in_dir, out_dir, flags, nth, thrank,)) \
				for thrank in range(nth)]
		for p in jobs: p.start()
		for p in jobs: p.join()
		for p in jobs: assert p.exitcode == 0


def submain(corpus_root, base_dir, in_dir, out_dir, flags=set(), nth=None, thrank=0):

	target       = f'purged_article'
	tmp_root     = f'data/tmp'
	base_root    = f'{corpus_root}/mention/{base_dir}'
	input_root   = f'{corpus_root}/mention/{in_dir}'
	output_root  = f'{corpus_root}/mention/{out_dir}'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(base_root))
	if nth: parts = parts[thrank:len(parts):nth]
	if not parts: return

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
				fin = open(input_file)
			except FileNotFoundError as e:
				printr(colored('0;33', e))
			except Exception as e:
				print()
				print(colored('1;31', e))
			else:
				for line in fin:
					data = json.loads(line)
					key = (int(data['sid']), int(data['mid']),)
					data.pop('sid', None)
					data.pop('mid', None)

					if len(flags) == 0:
						data = dict((attr, value,) for attr, value in data.items() if value)
					else:
						data = dict((attr, value,) for attr, value in data.items() if value and attr in flags)

					if key in data_dict:
						data_dict[key].update(data)
					else:
						print(colored('1;31', f'Unknown mention {input_file}:{key[0]}:{key[1]}!'))
				fin.close()

		with open(output_file, 'w') as fout:
			for data in data_dict.values():
				fout.write(json.dumps(data)+'\n')

	if not thrank: print()


if __name__ == '__main__':

	main()
	print()
	pass
