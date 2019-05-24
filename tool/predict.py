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

	argparser.add_argument('-c', '--corpus', required=True,
			help='store corpus data in directory "<CORPUS>/"')
	argparser.add_argument('-m', '--model',
			help='store model data in directory "<MODEL>/"; default is "<CORPUS>/model/"')
	argparser.add_argument('-o', '--output',
			help='output predicted XML articles into directory <OUTPUT>; default is "<CORPUS>/xml/purged_article_gnrid/"')

	argparser.add_argument('-s', '--structure-eem', choices=['c', 'cd', 'cn', 'cdn'], default='cdn', \
			help='use model structure <STRUCTURE-EEM> for entity embeddings model; default is "cdn"')
	# argparser.add_argument('-S', '--structure-mtc', choices=[''], default='cdn', \
	# 		help='use model structure <STRUCTURE-MTC> for mention type classifier')
	argparser.add_argument('-l', '--label-eem', choices=['gid', 'rid', 'joint'], default='joint', \
			help='use label type <LABEL-EEM> for entity embeddings model; default is "joint"')
	argparser.add_argument('-L', '--label-mtc', choices=['gid', 'rid', 'joint'], default='gid', \
			help='use label type <LABEL-MTC> for mention type classifier; default is "gid"')

	argparser.add_argument('-t', '--thread', type=int, \
			help='use <THREAD> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	model0 = 'model0'
	model1 = 'model1'+args.structure_eem
	label0 = args.label_mtc
	label1 = args.label_eem

	corpus_root = os.path.normpath(args.corpus)
	assert os.path.isdir(corpus_root)

	corpus_model_root = f'{corpus_root}/model'
	model_root = os.path.normpath(args.model if args.model else corpus_model_root)
	assert os.path.isdir(model_root)

	corpus_output_root = f'{corpus_root}/xml/purged_article_gnrid'
	output_root = os.path.normpath(args.output if args.output else corpus_output_root)
	os.makedirs(output_root, exist_ok=True)
	assert os.path.isdir(output_root)

	nth = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print()
	print(f'Thread Number : {nth}')
	print(f'Corpus Path   : {corpus_root}')
	print(f'Model Path    : {model_root}')
	print(f'Output Path   : {output_root}')
	print()
	print(f'Mention Type Classifier Label     : {", ".join(label0)}')
	print(f'Entity Embeddings Model Label     : {", ".join(label1)}')
	print(f'Entity Embeddings Model Structure : {args.structure_eem.upper()}')

	python = sys.executable

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                                  Prediction                                  #'))
	print(colored('1;96', '################################################################################'))
	print()
	subprocess.run([python, './model/predict.py', '-c', corpus_root, '-m', model_root, \
			'-i', 'purged_article_rid', '-o', 'purged_article_nrid', \
			'-l', label1, '-s', model1, '-L', label0, '-S', model0], check=True)

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                               Mention Merging                                #'))
	print(colored('1;96', '################################################################################'))
	print()
	subprocess.run([python, './util/mention_merge.py', '-c', corpus_root, '-t', str(nth), \
			'-b', 'purged_article_nrid', '-i', 'purged_article_gid', '-o', 'purged_article_gnrid', '-f', 'gid'], check=True)

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                                 XML Encoding                                 #'))
	print(colored('1;96', '################################################################################'))
	print()
	subprocess.run([python, './util/xml_encode.py', '-c', corpus_root, '-t', str(nth), \
			'-i', 'purged_article_gnrid', '-o', 'purged_article_gnrid'], check=True)

	if not os.path.samefile(output_root, corpus_output_root):
		print()
		print(colored('1;96', '################################################################################'))
		print(colored('1;96', '#                                   XML Copy                                   #'))
		print(colored('1;96', '################################################################################'))
		print()
		corpus_output_files = glob_files(corpus_output_root)
		n = str(len(corpus_output_files))
		for i, corpus_output_file in enumerate(corpus_output_files):
			output_file = transform_path(corpus_output_file, corpus_output_root, output_root)
			os.makedirs(os.path.dirname(output_file), exist_ok=True)
			shutil.copyfile(f'{corpus_output_file}', f'{output_file}')
			printr(f'{i+1:0{len(n)}}/{n}\tCopying "{output_file}"')
	print()

	print()
	print(colored('1;93', '********************************************************************************'))
	print(colored('1;93',f'* Output XML files to "{output_root}"'))
	print(colored('1;93', '*'))
	print()


if __name__ == '__main__':

	main()
	pass
