#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import itertools
import os
import sys

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

from xml_encode import add_start_xml
from xml_encode import add_end_xml


def get_html_idxs(mention):
	return (int(mention.sentence.tags[mention.start_idx].split(',')[0]), \
			int(mention.sentence.tags[mention.last_idx].split(',')[1]))


if __name__ == '__main__':

	assert len(sys.argv) > 1
	ver = sys.argv[1]

	target       = f'pruned_article'
	target_ver   = f''
	target_ver   = f'_gid'
	# target_ver   = f'_exact'
	data_root    = f'data/{ver}'
	repo_root    = f'{data_root}/repo'
	idx_root     = f'{data_root}/html/{target}_idx'
	html_root    = f'{data_root}/html/html_article'
	mention_root = f'{data_root}/mention/{target}{target_ver}'
	output_root  = f'{data_root}/html/{target}{target_ver}'
	parts        = ['']
	parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) > 2: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	# Load StyleMe repository and corpus
	corpus = Corpus(idx_root, mention_root, parts=parts)

	# Extract html from json
	html_files = grep_files(html_root, parts)
	n = str(len(html_files))
	for i, html_file in enumerate(html_files):
		output_file = transform_path(html_file, html_root, output_root, '.xml.html')
		os.makedirs(os.path.dirname(output_file), exist_ok=True)
		printr(f'{i+1:0{len(n)}}/{n}\t{output_file}')

		with open(html_file) as fin, open(output_file, 'w') as fout:
			output_data = list(fin.read())
			bundle = corpus.id_to_mention_bundle[Article.path_to_aid(html_file)]

			for mention in bundle:
				idx0, idx1 = get_html_idxs(corpus.id_to_mention[mention.ids])
				output_data[idx0] = add_start_xml(output_data[idx0], mention)
				output_data[idx1] = add_end_xml(output_data[idx1], mention)

			fout.write(''.join(output_data))
	print()

	pass
