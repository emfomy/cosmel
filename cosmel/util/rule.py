#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import os
import subprocess
import sys

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *


def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Annotate by Rule.')

	argparser.add_argument('-v', '--ver', metavar='<ver>#<cver>', required=True, \
			help='load repo from "data/<ver>", and load/save corpus data from/into "data/<ver>/corpus/<cver>"')
	argparser.add_argument('-t', '--thread', metavar='<thread>', type=int, \
			help='use <thread> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	vers = args.ver.split('#')
	assert len(vers) == 2, argparser.format_usage()
	ver  = vers[0]
	cver = vers[1]
	assert len(ver)  > 0
	assert len(cver) > 0

	nth = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print(f'Use {nth} threads')

	import multiprocessing
	with multiprocessing.Pool(nth) as pool:
		results = [pool.apply_async(submain, args=(ver, cver, nth, thrank,)) for thrank in range(nth)]
		[result.get() for result in results]
		del results


def submain(ver, cver, nth=None, thrank=0):

	data_root    = f'data/{ver}'
	corpus_root  = f'data/{ver}/corpus/{cver}'
	parsed_root  = f'{corpus_root}/article/parsed_article_parse'
	tmp_root     = f'{corpus_root}/article/parsed_article_parse1'
	xml_root     = f'{corpus_root}/xml/parsed_article_ws_rid'
	# parts        = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = sorted(rm_ext_all(file) for file in os.listdir(parsed_root))
	if nth: parts = parts[thrank:len(parts):nth]

	parsed_files = glob_files(parsed_root, parts=parts)
	n = str(len(parsed_files))
	for i, parsed_file in enumerate(parsed_files):
		tmp_file = transform_path(parsed_file, parsed_root, tmp_root, '.parse1')
		xml_file = transform_path(parsed_file, parsed_root, xml_root, '.xml')
		os.makedirs(os.path.dirname(tmp_file), exist_ok=True)
		os.makedirs(os.path.dirname(xml_file), exist_ok=True)
		printr(f'{i+1:0{len(n)}}/{n}\t{parsed_file}')

		subprocess.Popen(['util/rule_each.pl', ver, parsed_file, tmp_file, xml_file])
	if not thrank: print()


if __name__ == '__main__':

	main()
	print()
	pass
