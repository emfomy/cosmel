#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import os
import sys

sys.path.insert(0, os.path.abspath('.'))
from styleme import *

class RawMention:

	def __init__(self, article, s_id, m_id):
		self.article   = article
		self.s_id      = s_id
		self.m_id      = m_id

	def __str__(self):
		return '\t'.join(map(str, [self.s_id, self.m_id]))

	@property
	def sentence(self):
		return self.article[self.s_id]


def indices(lst, ele, start=0, end=None):
	return [i+start for i, val in enumerate(lst[start:end]) if val == ele]


if __name__ == '__main__':

	assert len(sys.argv) >= 2
	ver = sys.argv[1]

	greped_mention   = False
	written_sentence = True
	used_last_head   = False

	data_root     = f'data/{ver}'
	target        = f'prune_article_ws'
	article_root  = f'{data_root}/article/{target}'
	mention_root  = f'{data_root}/mention/{target}'
	repo_root     = f'{data_root}/repo'
	tmp_root      = f'data/tmp'
	parts         = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) >= 3: parts = list(f'part-{x:05}' for x in range(128) if x % 8 == int(sys.argv[2]))

	repo          = Repo(repo_root)
	articles      = ArticleSet(article_root, parts=parts)
	id_to_article = Id2Article(articles)

	max_len_mention = 10

	tmp_sentence_root = tmp_root+'/sentence_'+target

	mentions = dict()
	if not greped_mention:

		# Remove Temp Files
		rm_files(mention_root, parts=parts)

		# Grep mentions
		for article in articles:
			mention_list = []

			for s_id, line in enumerate(article):
				head_idxs = indices(line.tags, 'N_Head')
				if len(head_idxs):
					for m_id in head_idxs:
						mention_list.append(RawMention(article, s_id, m_id))
			mentions[article] = mention_list

			# Write mentions to file
			mention_file = article.path.replace(article_root, mention_root)+'.mention'
			os.makedirs(os.path.dirname(mention_file), exist_ok=True)
			printr(f'Writing {os.path.relpath(mention_file)}')
			with open(mention_file, 'w') as fout:
				for mention in mention_list:
					fout.write(str(mention)+'\n')
		print()

	else:
		# Load mentions from file
		for mention_file in grep_files(mention_root, parts=parts):
			article = id_to_article[Article.path_to_a_id(mention_root)]
			printr(f'Reading {os.path.relpath(mention_file)}')
			with open(mention_file) as fin:
				mention_list = []
				for line in fin:
					s_id, m_id = line.strip().split('\t')
					mention_list.append(RawMention(article, int(s_id), int(m_id)))
			mentions[article] = mention_list
		print()

	if not written_sentence:
		# Remove Temp Files
		rm_files(tmp_sentence_root, parts=parts)

		# Writhe mention sentences to file
		for article, mention_list in mentions.items():
			sentence_file = article.path.replace(article_root, tmp_sentence_root)+'.sentence'
			os.makedirs(os.path.dirname(sentence_file), exist_ok=True)
			printr(f'Writing {os.path.relpath(sentence_file)}')
			with open(sentence_file, 'w') as fout:
				for mention in mention_list:
					if len(mention.head_idxs) > 1:
						fout.write(str(mention.sentence)+'\n')
					else:
						fout.write('\n')
		print()

	pass
