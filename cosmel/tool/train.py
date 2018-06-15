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
	argparser = argparse.ArgumentParser(description='CosmEL Tool: Training.')

	argparser.add_argument('-c', '--corpus', required=True,
			help='store corpus data in directory "<CORPUS>/"')
	argparser.add_argument('-m', '--model',
			help='store model data in directory "<MODEL>/"; default is "<CORPUS>/model/"')
	argparser.add_argument('-x', '--xml',
			help='load golden labeled XML articles from directory <XML>; default is "<CORPUS>/xml/purged_article_gid/"')

	argparser.add_argument('--emb',
			help='load pretrained embeddings from file <EMB>; default is "<CORPUS>/embedding/purged_article.dim300.emb.bin"')
	argparser.add_argument('-s', '--structure-eem', choices=['c', 'cd', 'cn', 'cdn'], default='cdn', \
			help='use model structure <STRUCTURE-EEM> for entity embeddings model; default is "cdn"')
	# argparser.add_argument('-S', '--structure-mtc', choices=[''], default='cdn', \
	# 		help='use model structure <STRUCTURE-MTC> for mention type classifier')
	argparser.add_argument('-l', '--label-eem', choices=['gid', 'rid', 'joint'], nargs='*', default=['joint'], \
			help='use label type <LABEL-EEM> for entity embeddings model; default is "joint"')
	argparser.add_argument('-L', '--label-mtc', choices=['gid', 'rid', 'joint'], nargs='*', default=['gid'], \
			help='use label type <LABEL-MTC> for mention type classifier; default is "gid"')

	argparser.add_argument('-t', '--thread', type=int, \
			help='use <THREAD> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	corpus_root = os.path.normpath(args.corpus)
	assert os.path.isdir(corpus_root)

	corpus_model_root = f'{corpus_root}/model'
	model_root = os.path.normpath(args.model if args.model else corpus_model_root)
	os.makedirs(model_root, exist_ok=True)
	assert os.path.isdir(model_root)

	corpus_xml_root = f'{corpus_root}/xml/purged_article_gid'
	xml_root = os.path.normpath(args.xml if args.xml else corpus_xml_root)
	assert os.path.isdir(xml_root)

	emb_file = f'{corpus_root}/embedding/purged_article.dim300.emb.bin'
	if args.emb != None:
		emb_file = args.emb

	model0 = 'model0'
	model1 = 'model1'+args.structure_eem
	label0 = set(sorted(args.label_mtc))
	label1 = set(sorted(args.label_eem))

	assert len(label0)+len(label1) > 0

	nth = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print()
	print(f'Thread Number  : {nth}')
	print(f'Corpus Path    : {corpus_root}')
	print(f'Model Path     : {model_root}')
	print(f'XML Path       : {xml_root}')
	print(f'Embedding File : {emb_file}')
	print()
	print(f'Mention Type Classifier Label     : {label0}')
	print(f'Entity Embeddings Model Label     : {label1}')
	print(f'Entity Embeddings Model Structure : {args.structure_eem.upper()}')

	python = sys.executable

	if not os.path.exists(corpus_xml_root) or not os.path.samefile(xml_root, corpus_xml_root):
		print()
		print(colored('1;96', '################################################################################'))
		print(colored('1;96', '#                                   XML Copy                                   #'))
		print(colored('1;96', '################################################################################'))
		print()
		xml_files = glob_files(xml_root)
		n = str(len(xml_files))
		for i, xml_file in enumerate(xml_files):
			corpus_xml_file = transform_path(xml_file, xml_root, corpus_xml_root)
			os.makedirs(os.path.dirname(corpus_xml_file), exist_ok=True)
			shutil.copyfile(f'{xml_file}', f'{corpus_xml_file}')
			printr(f'{i+1:0{len(n)}}/{n}\tCopying "{corpus_xml_file}"')
	print()

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                                 XML Decoding                                 #'))
	print(colored('1;96', '################################################################################'))
	print()
	if subprocess.call([python, './util/xml_decode.py', '-c', corpus_root, '-t', str(nth), \
			'-i', 'purged_article_gid', '-o', 'purged_article_gid']): sys.exit()

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                               Mention Merging                                #'))
	print(colored('1;96', '################################################################################'))
	print()
	if subprocess.call([python, './util/mention_merge.py', '-c', corpus_root, '-t', str(nth), \
			'-b', 'purged_article_rid', '-i', 'purged_article_gid', '-o', 'purged_article_grid', '-f', 'gid']): sys.exit()

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                                Creating Meta                                 #'))
	print(colored('1;96', '################################################################################'))
	print()

	if subprocess.call([python, './model/meta.py', '-c', corpus_root, '-m', model_root, '--emb', emb_file]): sys.exit()

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                       Training Mention Type Classifier                       #'))
	print(colored('1;96', '################################################################################'))
	print()

	if 'rid' in label0 or 'joint' in label0:
		if subprocess.call([python, './model/train.py', '-c', corpus_root, '-m', model_root, \
				'-i', 'purged_article_grid', '-l', 'rid', '-s', model0]): sys.exit()
	if 'gid' in label0:
		if subprocess.call([python, './model/train.py', '-c', corpus_root, '-m', model_root, \
				'-i', 'purged_article_grid', '-l', 'gid', '-s', model0]): sys.exit()
	if 'joint' in label0:
		if subprocess.call([python, './model/train.py', '-c', corpus_root, '-m', model_root, \
				'-i', 'purged_article_grid', '-l', 'gid', '-p' 'rid', '-w', 'joint', '-s', model0]): sys.exit()

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                       Training Entity Embeddings Model                       #'))
	print(colored('1;96', '################################################################################'))
	print()

	if 'rid' in label1 or 'joint' in label1:
		if subprocess.call([python, './model/train.py', '-c', corpus_root, '-m', model_root, \
				'-i', 'purged_article_grid', '-l', 'rid', '-s', model1]): sys.exit()
	if 'gid' in label1:
		if subprocess.call([python, './model/train.py', '-c', corpus_root, '-m', model_root, \
				'-i', 'purged_article_grid', '-l', 'gid', '-s', model1]): sys.exit()
	if 'joint' in label1:
		if subprocess.call([python, './model/train.py', '-c', corpus_root, '-m', model_root, \
				'-i', 'purged_article_grid', '-l', 'gid', '-p' 'rid', '-w', 'joint', '-s', model1]): sys.exit()

	print()
	print(colored('1;93', '********************************************************************************'))
	print(colored('1;93',f'* Output model files to "{model_root}"'))
	print(colored('1;93', '*'))
	print()


if __name__ == '__main__':

	main()
	pass
