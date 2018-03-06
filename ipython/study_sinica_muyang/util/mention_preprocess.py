#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import os
import sys

sys.path.insert(0, os.path.abspath('.'))
from styleme import *


def indices(lst, ele, start=0, end=None):
	return [i+start for i, val in enumerate(lst[start:end]) if val == ele]


if __name__ == '__main__':

	assert len(sys.argv) >= 2
	ver = sys.argv[1]

	greped_mention   = False
	written_sentence = True

	target        = f'pruned_article'
	tmp_root      = f'data/tmp'
	data_root     = f'data/{ver}'
	article_root  = f'{data_root}/article/{target}_role'
	mention_root  = f'{data_root}/mention/{target}'
	sentence_root = f'{data_root}/parser/{target}'
	idx_root      = f'{data_root}/parser/{target}_idx'
	repo_root     = f'{data_root}/repo'
	parts         = ['']
	parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) >= 3: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	empty_file    = tmp_root+'/empty.tmp'

	articles = ArticleSet(article_root, parts=parts)

	max_len_mention = 10

	with open(empty_file, 'w'): pass

	# Grep mentions
	if not greped_mention:
		for article in articles:
			mention_file = transform_path(article.path, article_root, mention_root, '.mention')
			bundle = MentionBundle(empty_file, article)
			bundle._MentionBundle__data = [Mention(article, s_id, m_id) \
					for s_id, line in enumerate(article) for m_id in indices(line.roles, 'Head')]
			bundle.save(mention_file)
		print()

	if not written_sentence:

		bundles = MentionBundleSet(article_root, mention_root, articles)

		# Writhe mention sentences to file
		n = str(len(bundles))
		for i, bundle in enumerate(bundles):
			sentence_file = transform_path(bundle.path, mention_root, sentence_root, '.sentence')
			idx_file      = transform_path(sentence_file, sentence_root, idx_root) +'.idx'
			os.makedirs(os.path.dirname(sentence_file), exist_ok=True)
			os.makedirs(os.path.dirname(idx_file), exist_ok=True)
			printr(f'{i+1:0{len(n)}}/{n}\tWriting {os.path.relpath(sentence_file)}')
			with open(sentence_file, 'w') as fout_sentence, open(idx_file, 'w') as fout_idx:
				for mention in bundle:
					# for i in range(relu(mention.m_id-max_len_mention), mention.m_id):
					# 	if mention.sentence.roles[i] == 'Infix' and (mention.sentence.tags[i] == 'VC' or mention.sentence.tags[i] == 'VCL'):
					# 		mention.sentence.tags[i] = 'VH'
					# 		mention.sentence.roles[i] = colored('0;96', 'Infix*')
					fout_sentence.write(str(mention.sentence)+'\n')
					fout_idx.write(f'{mention.s_id, mention.m_id}\t{roledstr(mention)}\n')
		print()

	pass
