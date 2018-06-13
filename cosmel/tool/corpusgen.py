#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import os
import shutil
import subprocess
import sys

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *


def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL Tool: Corpus Generator.')

	argparser.add_argument('-c', '--corpus', required=True,
		help='store corpus data in directory "<CORPUS>/"')
	argparser.add_argument('-d', '--database',
		help='load product database from directory <DATABASE>; default is "<CORPUS>/repo/"')
	argparser.add_argument('-i', '--input',
		help='load articles in directory <INPUT>; default is "<CORPUS>/article/original_article/"')
	argparser.add_argument('-x', '--xml',
		help='output rule labeled XML articles into directory <XML>; default is "<CORPUS>/xml/purged_article_rid/"')

	arggroup = argparser.add_mutually_exclusive_group()

	arggroup.add_argument('-r', '--rule',
		help='use file <RULE> as rule')
	arggroup.add_argument('-e', '--rule-exact', action='store_true',
		help='use exact-match rule')

	argparser.add_argument('-t', '--thread', type=int, \
			help='use <THREAD> threads; default is `os.cpu_count()`')

	args = argparser.parse_args()

	corpus_root = os.path.normpath(args.corpus)
	os.makedirs(corpus_root, exist_ok=True)
	assert os.path.isdir(corpus_root)

	corpus_repo_root  = f'{corpus_root}/repo'
	repo_root = os.path.normpath(args.database if args.database else corpus_repo_root)
	assert os.path.isdir(repo_root)

	corpus_input_root = f'{corpus_root}/article/original_article'
	input_root = os.path.normpath(args.input if args.input else corpus_input_root)
	assert os.path.isdir(input_root)

	corpus_xml_root = f'{corpus_root}/xml/purged_article_rid'
	xml_root = os.path.normpath(args.xml if args.xml else corpus_xml_root)
	os.makedirs(xml_root, exist_ok=True)
	assert os.path.isdir(xml_root)

	rule_file = './util/rule.py'
	if args.rule_exact:
		rule_file = './util/rule_exact.py'
	if args.rule:
		rule_file = os.path.normpath(args.rule)
	assert os.path.isfile(rule_file)

	nth = args.thread
	if not nth: nth = os.cpu_count()

	print(args)
	print()
	print(f'Thread Number : {nth}')
	print(f'Corpus Path   : {corpus_root}')
	print(f'Database Path : {repo_root}')
	print(f'Input Path    : {input_root}')
	print(f'XML Path      : {xml_root}')
	print(f'Rule          : {rule_file}')

	python = sys.executable

	if not os.path.exists(corpus_repo_root) or not os.path.samefile(repo_root, corpus_repo_root):
		print()
		print(colored('1;96', '################################################################################'))
		print(colored('1;96', '#                                Database Copy                                 #'))
		print(colored('1;96', '################################################################################'))
		print()
		repo_files = glob_files(repo_root)
		n = str(len(repo_files))
		for i, repo_file in enumerate(repo_files):
			corpus_repo_file = transform_path(repo_file, repo_root, corpus_repo_root)
			os.makedirs(os.path.dirname(corpus_repo_file), exist_ok=True)
			shutil.copyfile(f'{repo_file}', f'{corpus_repo_file}')
			printr(f'{i+1:0{len(n)}}/{n}\tCopying "{corpus_repo_file}"')
	print()

	if not os.path.exists(corpus_input_root) or not os.path.samefile(input_root, corpus_input_root):
		print()
		print(colored('1;96', '################################################################################'))
		print(colored('1;96', '#                                 Article Copy                                 #'))
		print(colored('1;96', '################################################################################'))
		print()
		input_files = glob_files(input_root)
		n = str(len(input_files))
		for i, input_file in enumerate(input_files):
			corpus_input_file = transform_path(input_file, input_root, corpus_input_root)
			os.makedirs(os.path.dirname(corpus_input_file), exist_ok=True)
			shutil.copyfile(f'{input_file}', f'{corpus_input_file}')
			printr(f'{i+1:0{len(n)}}/{n}\tCopying "{corpus_input_file}"')
	print()

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                              Article Processing                              #'))
	print(colored('1;96', '################################################################################'))
	print()
	if subprocess.call([python, './util/article_preprocess.py', '-c', corpus_root, '-t', str(nth)]): sys.exit()
	print()

	if subprocess.call([python, './util/article_postprocess.py', '-c', corpus_root, '-t', str(nth)]): sys.exit()

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                              Mention Detection                               #'))
	print(colored('1;96', '################################################################################'))
	print()
	if subprocess.call([python, './util/mention_detect.py', '-c', corpus_root, '-t', str(nth)]): sys.exit()

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                               Rule Annotation                                #'))
	print(colored('1;96', '################################################################################'))
	print()

	if subprocess.call([python, rule_file, '-c', corpus_root, '-t', str(nth)]): sys.exit()

	print()
	print(colored('1;96', '################################################################################'))
	print(colored('1;96', '#                                 XML Encoding                                 #'))
	print(colored('1;96', '################################################################################'))
	print()
	if subprocess.call([python, './util/xml_encode.py', '-c', corpus_root, '-t', str(nth), \
			'-i', 'purged_article_rid', '-o', 'purged_article_rid']): sys.exit()

	if not os.path.samefile(xml_root, corpus_xml_root):
		print()
		print(colored('1;96', '################################################################################'))
		print(colored('1;96', '#                                   XML Copy                                   #'))
		print(colored('1;96', '################################################################################'))
		print()
		corpus_xml_files = glob_files(corpus_xml_root)
		n = str(len(corpus_xml_files))
		for i, corpus_xml_file in enumerate(corpus_xml_files):
			xml_file = transform_path(corpus_xml_file, corpus_xml_root, xml_root)
			os.makedirs(os.path.dirname(xml_file), exist_ok=True)
			shutil.copyfile(f'{corpus_xml_file}', f'{xml_file}')
			printr(f'{i+1:0{len(n)}}/{n}\tCopying "{xml_file}"')
	print()

	print()
	print(colored('1;93', '********************************************************************************'))
	print(colored('1;93',f'* Please modify "gid" flags in "{xml_root}" if you need manual annotation.'))
	print(colored('1;93', '*'))
	print()


if __name__ == '__main__':

	main()
	pass
