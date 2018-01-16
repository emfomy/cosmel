#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import multiprocessing
import os
import shutil

import time

from styleme import *


class RawMention:

	def __init__(self, article, s_id, begin_idx, end_idxs):
		self.article   = article
		self.s_id      = s_id
		self.begin_idx = begin_idx
		self.end_idxs  = end_idxs

	def __str__(self):
		return '\t'.join(map(str, [self.s_id, self.begin_idx, ','.join(map(str, self.end_idxs))]))

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
	articles     = ArticleSet(article_path)
	path2article = Path2Article(articles)

	max_len_mention = 10

	tmp_mention_path  = tmp_path+'/mention'+target
	tmp_sentence_path = tmp_path+'/sentence'+target

	if not greped_mention:

		# Remove Temp Files
		if os.path.exists(tmp_mention_path):
			shutil.rmtree(tmp_mention_path)

		# Grep mentions
		def __func(article, article_path, tmp_mention_path):
			mention_list = []

			for s_id, line in enumerate(article):
				idx = -1
				while True:
					try:
						idx = line.tags.index('N_Brand', idx+1)
					except ValueError:
						break
					end_idxs = indices(line.tags, 'N_Head', idx+1, idx+max_len_mention)
					if len(end_idxs):
						mention_list.append(RawMention(article, s_id, idx, end_idxs))
						idx = end_idxs[-1]

			# Write mentions to file
			tmp_mention_file = article.path.replace(article_path, tmp_mention_path)+'.mention'
			os.makedirs(os.path.dirname(tmp_mention_file), exist_ok=True)
			printr('Writing {}'.format(os.path.relpath(tmp_mention_file)))
			with open(tmp_mention_file, 'w') as fout:
				for mention in mention_list:
					fout.write(str(mention)+'\n')

			return (article, mention_list)

		with multiprocessing.Pool() as pool:
			results  = [pool.apply_async(__func, args=(article, article_path, tmp_mention_path,)) for article in articles]
			mentions = dict([result.get() for result in results])
			del results
		print()

	else:
		# Load mentions from file
		def __func(tmp_mention_file, tmp_mention_path, article_path):
			path = tmp_mention_file.replace(tmp_mention_path, article_path)[:-len('.mention')]
			article = path2article[path]
			printr('Reading {}'.format(os.path.relpath(tmp_mention_file)))
			with open(tmp_mention_file) as fin:
				mention_list = []
				for line in fin:
					s_id, begin_idx, end_idxs_str = line.strip().split('\t')
					mention_list.append(RawMention(article, int(s_id), int(begin_idx), list(map(int, end_idxs_str.split(',')))))
			return (article, mention_list)

		with multiprocessing.Pool() as pool:
			results  = [pool.apply_async(__func, args=(tmp_mention_file, tmp_mention_path, article_path,)) \
					for tmp_mention_file in grep_files(tmp_mention_path)]
			mentions = dict([result.get() for result in results])
			del results
		print()

	if not written_sentence:
		# Remove Temp Files
		if os.path.exists(tmp_sentence_path):
			shutil.rmtree(tmp_sentence_path)

		# Writhe mention sentences to file
		def __func(article, mention_list, article_path, tmp_sentence_path):
			sentence_file = article.path.replace(article_path, tmp_sentence_path)+'.sentence'
			os.makedirs(os.path.dirname(sentence_file), exist_ok=True)
			printr('Writing {}'.format(os.path.relpath(sentence_file)))
			with open(sentence_file, 'w') as fout:
				for mention in mention_list:
					if len(mention.end_idxs) > 1:
						fout.write(str(mention.sentence)+'\n')
					else:
						fout.write('\n')

		with multiprocessing.Pool() as pool:
			results = [pool.apply_async(__func, args=(article, mention_list, article_path, tmp_sentence_path)) \
					for article, mention_list in mentions.items()]
			[result.get() for result in results]
			del results
		print()

	if not parsed:
		pass

	if not used_last_head:

		# Write mentions to file
		def __func(article, mention_list, article_path, mention_path):
			mention_file = article.path.replace(article_path, mention_path)+'.mention'
			os.makedirs(os.path.dirname(mention_file), exist_ok=True)
			printr('Writing {}'.format(os.path.relpath(mention_file)))
			with open(mention_file, 'w') as fout:
				for mention in mention_list:
					mention.end_idxs = [mention.end_idxs[-1]]
					fout.write(str(mention)+'\n')

		with multiprocessing.Pool() as pool:
			results = [pool.apply_async(__func, args=(article, mention_list, article_path, mention_path,)) \
					for article, mention_list in mentions.items()]
			[result.get() for result in results]
			del results
		print()

	pass
