#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import collections.abc
import itertools
import os

from styleme.util import *
from styleme.corpus.article import *


class Mention:
	"""The mention class.

	Args:
		article       (:class:`.Article`):    the article containing this mention.
		name_to_brand (:class:`.Name2Brand`): the dictionary maps brand name to brand object.
		s_id          (int):                  the line index in the aritcle.
		brand_idx     (int):                  the brand index in the sentence.
		head_idx      (int):                  the head index in the sentence.
		p_id          (str):                  the product ID.
		g_id          (str):                  the golden product ID.
	"""

	def __init__(self, name_to_brand, article, s_id, brand_idx, head_idx, p_id='', g_id='', rule=''):
		super().__init__()

		self.__article   = article
		self.__s_id      = int(s_id)
		self.__brand_idx = int(brand_idx)
		self.__head_idx  = int(head_idx)
		self.__p_id      = p_id
		self.__g_id      = g_id
		self.__rule      = rule
		self.__brand     = name_to_brand[self.b_name]

	def __str__(self):
		return str(self.mention)

	def __repr__(self):
		return repr(self.mention)

	def __txtstr__(self):
		return txtstr(self.mention)

	def __hash__(self):
		return hash(ids)

	@property
	def article(self):
		""":class:`.Article`: the article containing this mention."""
		return self.__article

	@property
	def sentence(self):
		""":class:`.WsWords`: the sentence containing this mention."""
		return self.__article[self.__s_id]

	@property
	def mention(self):
		""":class:`.WsWords`: this mention."""
		return self.sentence[self.slice]

	@property
	def ids(self):
		"""tuple: the tuple of article ID, sentence ID, and mention ID."""
		return (self.a_id, self.s_id, self.m_id,)

	@property
	def a_id(self):
		"""str: the article ID."""
		return self.__article.a_id

	@property
	def s_id(self):
		"""int: the sentence ID (the line index in the article)."""
		return self.__s_id

	@property
	def m_id(self):
		"""int: the mention ID (= :attr:`brand_idx`)."""
		return self.__brand_idx

	@property
	def brand_idx(self):
		"""int: the brand index in the sentence."""
		return self.__brand_idx

	@property
	def head_idx(self):
		"""int: the head index in the sentence."""
		return self.__head_idx

	@property
	def beginning_idx(self):
		"""int: the beginning index in the sentence (= :attr:`brand_idx`)."""
		return self.__brand_idx

	@property
	def ending_idx(self):
		"""int: the ending index in the sentence (= :attr:`head_idx` +1)."""
		return self.__head_idx+1

	@property
	def slice(self):
		"""slice: the mention slice index in the sention (= :attr:`beginning_idx` : :attr:`ending_idx`)."""
		return slice(self.beginning_idx, self.ending_idx)

	@property
	def p_id(self):
		"""str: the product ID."""
		return self.__p_id

	@property
	def g_id(self):
		"""str: the golden product ID."""
		return self.__g_id

	@property
	def rule(self):
		"""str: the rule for the product ID."""
		return self.__rule

	@property
	def brand(self):
		""":class:`.Brand`: the brand."""
		return self.__brand

	@property
	def b_name(self):
		"""str: the brand name."""
		return self.sentence.txts[self.__brand_idx]

	@property
	def name(self):
		"""str: the name (excluding brand)."""
		return txtstr(self.name_ws)

	@property
	def head(self):
		"""str: the head word."""
		return self.sentence.txts[self.__head_idx]

	@property
	def head_list(self):
		"""str: the head word lists."""
		return [self.mention.txts[i] for i, tag in enumerate(self.mention.tags) if tag == 'N_Head']

	@property
	def name_ws(self):
		""":class:`.WsWords`: the word-segmented name (excluding brand)."""
		return self.sentence[self.beginning_idx+1:self.ending_idx]

	@property
	def infix_ws(self):
		""":class:`.WsWords`: the word-segmented infix (excluding brand and head)."""
		return self.sentence[self.beginning_idx+1:self.head_idx]

	@property
	def beginning_xml(self):
		"""str: the beginning XML tag."""
		return f'<product pid="{self.p_id}" gid="{self.g_id}" sid="{self.s_id}" mid="{self.m_id}" rule="{self.rule}">'

	def beginning_xml_(self, **kwargs):
		"""str: the beginning XML tag with custom tags."""
		return ' '.join([self.beginning_xml[:-1]] + [f'{key}="{kwargs[key]}"' for key in kwargs]) + '>'

	@property
	def ending_xml(self):
		"""str: the ending XML tag."""
		return f'</product>'

	@property
	def filestr(self):
		"""Change to string for file."""
		return '\t'.join([str(self.__s_id), str(self.__brand_idx), str(self.__head_idx), self.__p_id, self.__g_id, self.__rule])

	def set_p_id(self, p_id):
		"""Sets the product ID."""
		self.__p_id = p_id

	def set_g_id(self, g_id):
		"""Sets the golden product ID."""
		self.__g_id = g_id

	def set_rule(self, rule):
		"""Sets the rule for the product ID."""
		self.__rule = rule


class MentionSet(collections.abc.Collection):
	"""The set of mentions.

	* Item: mention (:class:`.Mention`)

	Args:
		mention_bundles (:class:`.MentionBundleSet`): the set of mention bundles.
	"""

	def __init__(self, mention_bundles):
		super().__init__()
		self.__data = list(itertools.chain.from_iterable(mention_bundles))

	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)


class MentionBundle(collections.abc.Sequence):
	"""The bundle of mentions in an article.

	* Item: mention (:class:`.Mention`)

	Args:
		file_path (str):             the path to the mention bundle.
		article (:class:`.Article`): the article containing this mention bundle.
		repo    (:class:`.Repo`):    the product repository class.
	"""

	def __init__(self, file_path, article, repo):
		super().__init__()

		printr(f'Reading {file_path}')
		with open(file_path) as fin:
			self.__data = [Mention(repo.name_to_brand, article, *tuple(line.strip().split('\t'))) for line in fin]

		self.__article = article
		self.__path    = file_path

	def __contains__(self, item):
		return item in self.__data

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def __str__(self):
		return str(list(str(item) for item in self.__data))

	def __repr__(self):
		return str(self.__data)

	def __hash__(self):
		return hash(self.a_id)

	@property
	def article(self):
		""":class:`.Article`: the article containing this mention."""
		return self.__article

	@property
	def a_id(self):
		"""str: the article ID (with leading author name and underscore)."""
		return self.__article.a_id

	@property
	def path(self):
		"""str: the related file path."""
		return self.__path

	def save(self, file_path):
		"""Save the mention bundle to file."""
		os.makedirs(os.path.dirname(file_path), exist_ok=True)
		printr(f'Writing {os.path.relpath(file_path)}')
		with open(file_path, 'w') as fout:
			for mention in self:
				fout.write(mention.filestr+'\n')


class MentionBundleSet(collections.abc.Collection):
	"""The set of mention bundles.

	* Item: mention bundle (:class:`.MentionBundle`)

	Args:
		article_root (str):                 the path to the folder containing word segmented article files.
		mention_root (str):                 the path to the folder containing mention files.
		article_set (:class:`.ArticleSet`): the set of articles.
		repo        (:class:`.Repo`):       the product repository class.
	"""

	def __init__(self, article_root, mention_root, article_set, repo):
		super().__init__()
		self.__data = [self._mention_bundle(article, article_root, mention_root, repo) for article in article_set]
		self.__path = mention_root
		print()

	@staticmethod
	def _mention_bundle(article, article_root, mention_root, repo):
		file_path = article.path.replace(article_root, mention_root)+'.mention'
		return MentionBundle(file_path, article, repo)

	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def save(self, output_root):
		"""Save all mention bundles to files."""
		for bundle in self:
			file_path = bundle.path.replace(self.__path, output_root)
			bundle.save(file_path)
		print()


class Id2Mention(collections.abc.Mapping):
	"""The dictionary maps article ID, sentence ID, and mention ID to mention object.

	* Key:  the article ID (str).
	* Item: the mention object (:class:`.Mention`).

	Args:
		mention_set (:class:`.MentionSet`): the mention set.
	"""

	def __init__(self, mention_set):
		super().__init__()
		self.__data = dict((mention.ids, mention,) for mention in mention_set)

	def __contains__(self, key):
		return key in self.__data

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)


class Article2MentionBundle(collections.abc.Mapping):
	"""The dictionary maps article object to mention bundle.

	* Key:  the article object (:class:`.Article`).
	* Item: the mention bundle (:class:`.MentionBundle`).

	Args:
		mention_bundle_set (:class:`.MentionBundleSet`): the mention bundle set.
	"""

	def __init__(self, mention_bundle_set):
		super().__init__()
		self.__data = dict((mention_bundle.article, mention_bundle,) for mention_bundle in mention_bundle_set)
		self.__empty_collection = ReadOnlyList()

	def __contains__(self, key):
		return key in self.__data

	def __getitem__(self, key):
		return self.__data.get(key, self.__empty_collection)

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)


class Id2MentionBundle(collections.abc.Sequence):
	"""The dictionary maps article ID to mention bundle.

	* Key:  the article ID (str).
	* Item: the mention bundle (:class:`.MentionBundle`).

	Args:
		article_to_mention_bundle (:class:`.Article2MentionBundle`): the dictionary maps article object to mention bundle.
		id_to_article             (:class:`.Id2Article`):            the dictionary maps article ID to article object.
	"""

	def __init__(self, article_to_mention_bundle, id_to_article):
		super().__init__()
		self.__data = article_to_mention_bundle
		self.__key  = id_to_article

	def __contains__(self, key):
		return self.__key[key] in self.__data

	def __getitem__(self, key):
		return self.__data[self.__key[key]]

	def __iter__(self):
		return iter(self.__data.values())

	def __len__(self):
		return len(self.__data)


class BrandHead2MentionList(collections.abc.Mapping):
	"""The dictionary maps brand object and head word to mention object list.

	* Key:  tuple of brand object (:class:`.Brand`) and mention head word (str).
	* Item: :class:`.ReadOnlyList` of mention object (:class:`.Mention`).

	Args:
		mention_set (:class:`.MentionSet`): the mention set.
	"""

	def __init__(self, mention_set):
		super().__init__()
		self.__data = dict()

		mention_dict = dict()
		for mention in mention_set:
			pair = (mention.brand, mention.head,)
			if pair not in mention_dict:
				mention_dict[pair] = [mention]
			else:
				mention_dict[pair] += [mention]

		for pair, mention_set in mention_dict.items():
			self.__data[pair] = ReadOnlyList(mention_set)

		self.__empty_collection = ReadOnlyList()

	def __contains__(self, key):
		return key in self.__data

	def __getitem__(self, key):
		return self.__data.get(key, self.__empty_collection)

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)


class NameHead2MentionList(collections.abc.Sequence):
	"""The dictionary maps brand name and head word to mention object list.

	* Key:  tuple of brand name (str) and mention head word (str).
	* Item: :class:`.ReadOnlyList` of mention object (:class:`.Mention`).

	Args:
		brand_head_to_mention_list (:class:`.BrandHead2Mentionlist`):
			the dictionary maps brand object and head word to mention object list.
		name_to_brand              (:class:`.Name2Brand`):
			the dictionary maps name and brand.
	"""

	def __init__(self, brand_head_to_mention_list, name_to_brand):
		super().__init__()
		self.__data = brand_head_to_mention_list
		self.__key  = name_to_brand

	def __contains__(self, key):
		return (self.__key[key[0]], key[1]) in self.__data

	def __getitem__(self, key):
		return self.__data[self.__key[key[0]], key[1]]

	def __iter__(self):
		return iter(self.__data.values())

	def __len__(self):
		return len(self.__data)

