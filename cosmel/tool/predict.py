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
	argparser = argparse.ArgumentParser(description='CosmEL Tool: Prediction.')

	argparser.add_argument('-v', '--ver', metavar='<ver>#<cver>#<mver>', required=True, \
		help='load repo from "data/<ver>/", load corpus data from "data/<ver>/corpus/<cver>/", ' + \
				'and load/save model data from/into "data/<ver>/model/<mver>/"; the default value of <mver> is <cver>')
	argparser.add_argument('-t', '--thread', metavar='<thread>', type=int, \
			help='use <thread> threads; default is `os.cpu_count()`')

	argparser.add_argument('-w', '--weight', metavar='<weight_name>', default='gid', \
			help='load model weight "data/<ver>/model/<mver>/<weight_name>.<model_type>.weight.pt"')
	argparser.add_argument('-m', '--model', metavar='<model_type>', default='model2cdn', \
			help='use model <model_type>')

	argparser.add_argument('-w0', '--weight0', metavar='<weight0_name>', default='gid', \
			help='load model weight "data/<ver>/model/<mver>/<weight_0name>.<model0_type>.weight.pt"')
	argparser.add_argument('-m0', '--model0', metavar='<model0_type>', default='model0', \
		  help='use model <model0_type>; default is "model0"')

	argparser.add_argument('-q', '--quiet', action='store_true', \
			help='quiet mode')

	args = argparser.parse_args()

	vers = args.ver.split('#')
	assert 2 <= len(vers) <= 3, argparser.format_usage()
	ver  = vers[0]
	cver = vers[1]
	mver = vers[-1]
	assert len(ver)  > 0
	assert len(cver) > 0
	assert len(mver) > 0

	weight  = args.weight
	model   = args.model
	weight0 = args.weight0
	model0  = args.model0

	nth = args.thread
	if not nth: nth = os.cpu_count()

	do_quiet = args.quiet

	print(args)
	print(f'Use {nth} threads')

	submain(ver, cver, mver, weight, model, weight0, model0, nth, do_quiet)

def submain(ver, cver, mver, weight, model, weight0, model0, nth, do_quiet):

	python = sys.executable
	stdout = subprocess.DEVNULL if do_quiet else None

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                                 XML Decoding                                 #'))
	print(colored('1;96', '################################################################################'))
	print()
	subprocess.call([python, './util/xml_encode.py', '-v', f'{ver}#{cver}', '-t', f'{nth}', \
			'-i', 'purged_article_rid'], stdout=stdout)

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                                  Prediction                                  #'))
	print(colored('1;96', '################################################################################'))
	print()
	subprocess.call([python, './model/predict.py', '-v', f'{ver}#{cver}#{mver}', \
			'-i', 'purged_article_rid', '-w', weight, '-m', model, '-w0', weight0, '-m0', model0], stdout=stdout)

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                                 XML Encoding                                 #'))
	print(colored('1;96', '################################################################################'))
	print()
	subprocess.call([python, './util/xml_encode.py', '-v', f'{ver}#{cver}', '-t', f'{nth}', \
			'-i', 'purged_article_nid'], stdout=stdout)


if __name__ == '__main__':

	main()
	print()
	pass
