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
	argparser = argparse.ArgumentParser(description='CosmEL: Annotate by Rule (Parser).')

	argparser.add_argument('-c', '--corpus', required=True,
			help='store corpus data in directory "<CORPUS>/"')
	argparser.add_argument('-t', '--thread', type=int, \
			help='use <THREAD> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	corpus_root = os.path.normpath(args.corpus)

	nth = args.thread
	if not nth: nth = os.cpu_count()

	# print(args)
	# print(f'Use {nth} threads')

	python = sys.executable

	############################################################################################################################
	host = '172.16.1.64'
	port = '6400'
	############################################################################################################################

	subprocess.run([python, './util/parse.py', '-c', corpus_root, '-t', str(nth), \
			'--host', host, '--port', port], check=True)
	subprocess.run([python, './util/rule_core.py', '-c', corpus_root, '-t', str(nth)], check=True)
	subprocess.run([python, './util/xml_decode.py', '-c', corpus_root, '-t', str(nth), \
			'-iw', 'parsed_article_ws_rid', '-i', 'parsed_article_rid', '-o', 'purged_article_rid'], check=True)


if __name__ == '__main__':

	main()
	print()
	pass
