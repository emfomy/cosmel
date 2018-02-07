#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
   Mu Yang <emfomy@gmail.com>
"""

import os
import sys

sys.path.insert(0, os.path.abspath('.'))
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
	mention_root  = f'{data_root}/mention/{target}'
	article_root  = f'{data_root}/article/{target}'
	repo_root     = f'{data_root}/repo'
	tmp_root      = f'data/tmp'
	parts         = ['']
	# parts        = list(f'part-{x:05}' for x in range(1))
	parts        = list(f'part-{x:05}' for x in range(128) if x % 8 == int(sys.argv[2]))

	repo          = Repo(repo_root)
	articles      = ArticleSet(article_root, parts=parts)
	id_to_article = Id2Article(articles)

	max_len_mention = 10

	tmp_mention_root  = tmp_root+'/mention_'+target
	tmp_sentence_root = tmp_root+'/sentence_'+target

	mentions = dict()
	if not greped_mention:

		# Remove Temp Files
		rm_files(tmp_mention_root, parts=parts)

		# Grep mentions
		for article in articles:
			mention_list = []

			for s_id, line in enumerate(article):
				brand_idxs = indices(line.tags, 'N_Brand')
				if len(brand_idxs):
					for brand_idx, next_idx in zip(brand_idxs, brand_idxs[1:]+[len(line.tags)]):
						head_idxs = indices(line.tags, 'N_Head', brand_idx+1, min(brand_idx+max_len_mention, next_idx))
						if len(head_idxs):
							mention_list.append(RawMention(article, s_id, brand_idx, head_idxs))
			mentions[article] = mention_list

			# Write mentions to file
			tmp_mention_file = article.path.replace(article_root, tmp_mention_root)+'.mention'
			os.makedirs(os.path.dirname(tmp_mention_file), exist_ok=True)
			printr(f'Writing {os.path.relpath(tmp_mention_file)}')
			with open(tmp_mention_file, 'w') as fout:
				for mention in mention_list:
					fout.write(str(mention)+'\n')
		print()

	else:
		# Load mentions from file
		for tmp_mention_file in grep_files(tmp_mention_root, parts=parts):
			article = id_to_article[Article.path_to_a_id(tmp_mention_root)]
			printr(f'Reading {os.path.relpath(tmp_mention_file)}')
			with open(tmp_mention_file) as fin:
				mention_list = []
				for line in fin:
					s_id, brand_idx, head_idxs_str = line.strip().split('\t')
					mention_list.append(RawMention(article, int(s_id), int(brand_idx), list(map(int, head_idxs_str.split(',')))))
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

	if not used_last_head:

		# Write mentions to file
		for article, mention_list in mentions.items():
			mention_file = article.path.replace(article_root, mention_root)+'.mention'
			os.makedirs(os.path.dirname(mention_file), exist_ok=True)
			printr(f'Writing {os.path.relpath(mention_file)}')
			with open(mention_file, 'w') as fout:
				for mention in mention_list:
					mention.head_idxs = [mention.head_idxs[-1]]
					fout.write(str(mention)+'\n')
		print()

	pass
