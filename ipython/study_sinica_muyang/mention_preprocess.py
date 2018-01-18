#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import os
import shutil

from styleme import *


class RawMention:

	def __init__(self, article, s_id, brand_idx, head_idxs):
		self.article   = article
		self.s_id      = s_id
		self.brand_idx = brand_idx
		self.head_idxs = head_idxs

	def __str__(self):
		return '\t'.join(map(str, [self.s_id, self.brand_idx, ','.join(map(str, self.head_idxs))]))

	@property
	def sentence(self):
		return self.article[self.s_id]


def indices(lst, ele, start, end = None):
	return [i+start for i, val in enumerate(lst[start:end]) if val == ele]


if __name__ == '__main__':

	greped_mention   = True
	written_sentence = True
	parsed           = True
	used_last_head   = False

	target        = '/prune_article_ws'
	mention_path  = 'data/mention'+target
	article_path  = 'data/article'+target
	repo_path     = 'data/repo'
	tmp_path      = 'data/tmp'

	repo         = Repo(repo_path)
	articles     = ArticleSet(article_path, ignore_duplicated=True)
	path_to_article = Path2Article(articles)

	max_len_mention = 10

	tmp_mention_path  = tmp_path+'/mention'+target
	tmp_sentence_path = tmp_path+'/sentence'+target

	mentions = dict()
	if not greped_mention:

		# Remove Temp Files
		if os.path.exists(tmp_mention_path):
			shutil.rmtree(tmp_mention_path)

		# Grep mentions
		for article in articles:
			mention_list = []

			for s_id, line in enumerate(article):
				idx = -1
				while True:
					try:
						idx = line.tags.index('N_Brand', idx+1)
					except ValueError:
						break
					head_idxs = indices(line.tags, 'N_Head', idx+1, idx+max_len_mention)
					if len(head_idxs):
						mention_list.append(RawMention(article, s_id, idx, head_idxs))
						idx = head_idxs[-1]
			mentions[article] = mention_list

			# Write mentions to file
			tmp_mention_file = article.path.replace(article_path, tmp_mention_path)+'.mention'
			os.makedirs(os.path.dirname(tmp_mention_file), exist_ok=True)
			printr('Writing {}'.format(os.path.relpath(tmp_mention_file)))
			with open(tmp_mention_file, 'w') as fout:
				for mention in mention_list:
					fout.write(str(mention)+'\n')
		print()

	else:
		# Load mentions from file
		for tmp_mention_file in grep_files(tmp_mention_path):
			path = tmp_mention_file.replace(tmp_mention_path, article_path)[:-len('.mention')]
			article = path_to_article[path]
			printr('Reading {}'.format(os.path.relpath(tmp_mention_file)))
			with open(tmp_mention_file) as fin:
				mention_list = []
				for line in fin:
					s_id, brand_idx, head_idxs_str = line.strip().split('\t')
					mention_list.append(RawMention(article, int(s_id), int(brand_idx), list(map(int, head_idxs_str.split(',')))))
			mentions[article] = mention_list
		print()

	if not written_sentence:
		# Remove Temp Files
		if os.path.exists(tmp_sentence_path):
			shutil.rmtree(tmp_sentence_path)

		# Writhe mention sentences to file
		for article, mention_list in mentions.items():
			sentence_file = article.path.replace(article_path, tmp_sentence_path)+'.sentence'
			os.makedirs(os.path.dirname(sentence_file), exist_ok=True)
			printr('Writing {}'.format(os.path.relpath(sentence_file)))
			with open(sentence_file, 'w') as fout:
				for mention in mention_list:
					if len(mention.head_idxs) > 1:
						fout.write(str(mention.sentence)+'\n')
					else:
						fout.write('\n')
		print()

	if not parsed:
		pass

	if not used_last_head:

		# Write mentions to file
		for article, mention_list in mentions.items():
			mention_file = article.path.replace(article_path, mention_path)+'.mention'
			os.makedirs(os.path.dirname(mention_file), exist_ok=True)
			printr('Writing {}'.format(os.path.relpath(mention_file)))
			with open(mention_file, 'w') as fout:
				for mention in mention_list:
					mention.head_idxs = [mention.head_idxs[-1]]
					fout.write(str(mention)+'\n')
		print()

	pass
