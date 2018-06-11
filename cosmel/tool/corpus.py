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
	argparser = argparse.ArgumentParser(description='CosmEL Tool: Create Corpus.')

	argparser.add_argument('-v', '--ver', metavar='<ver>#<cver>', required=True, \
			help='load repo from "data/<ver>", and load/save corpus data from/into "data/<ver>/corpus/<cver>"')
	argparser.add_argument('-t', '--thread', metavar='<thread>', type=int, \
			help='use <thread> threads; default is `os.cpu_count()`')
	argparser.add_argument('-q', '--quiet', action='store_true', \
			help='quiet mode')

	args = argparser.parse_args()

	vers = args.ver.split('#')
	assert len(vers) == 2, argparser.format_usage()
	ver  = vers[0]
	cver = vers[1]
	assert len(ver)  > 0
	assert len(cver) > 0

	nth = args.thread
	if not nth: nth = os.cpu_count()

	do_quiet = args.quiet

	print(args)
	print(f'Use {nth} threads')

	submain(ver, cver, nth, do_quiet)

def submain(ver, cver, nth, do_quiet):

	python = sys.executable
	stdout = subprocess.DEVNULL if do_quiet else None

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                            Article Preprocessing                             #'))
	print(colored('1;96', '################################################################################'))
	print()
	subprocess.call([python, './util/article_preprocess.py', '-v', f'{ver}#{cver}', '-t', f'{nth}'], stdout=stdout)

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                            Article Postprocessing                            #'))
	print(colored('1;96', '################################################################################'))
	print()
	subprocess.call([python, './util/article_postprocess.py', '-v', f'{ver}#{cver}', '-t', f'{nth}'], stdout=stdout)

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                            Mention Preprocessing                             #'))
	print(colored('1;96', '################################################################################'))
	print()
	subprocess.call([python, './util/mention_preprocess.py', '-v', f'{ver}#{cver}', '-t', f'{nth}'], stdout=stdout)

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                               Rule Annotation                                #'))
	print(colored('1;96', '################################################################################'))
	print()
	subprocess.call([python, './util/rule_exact.py', '-v', f'{ver}#{cver}', '-t', f'{nth}'], stdout=stdout)

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                                 XML Encoding                                 #'))
	print(colored('1;96', '################################################################################'))
	print()
	subprocess.call([python, './util/xml_encode.py', '-v', f'{ver}#{cver}', '-t', f'{nth}', \
			'-i', 'purged_article_rid'], stdout=stdout)


if __name__ == '__main__':

	main()
	print()
	pass
