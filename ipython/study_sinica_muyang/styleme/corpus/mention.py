#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import collections.abc
import itertools
import json
import os

from styleme.util import *
from styleme.corpus.article import *


class Mention:
	"""The mention class.

	Args:
		article (:class:`.Article`): the article containing this mention.
		sid     (int):               the sentence index in the aritcle.
		mid     (int):               the mention index in the sentence.
		pid     (str):               the product ID.
		gid     (str):               the golden product ID.
		rule    (str):               the rule.
		idxs    (slice):             the indix slice of this mention.
	"""

	def __init__(self, article, sid, mid, pid='', gid='', rule='', start=None, end=None, **kwargs):
		super().__init__()

		self.__article = article
		self.__sid     = int(sid)
		self.__mid     = int(mid)
		self.__pid     = pid
		self.__gid     = gid
		self.__rule    = rule
		self.__start   = start if start else self.__mid
		self.__end     = end   if end   else self.__mid+1
		self.__kwargs  = kwargs

	def __str__(self):
		return f'{str(self.sentence_pre)}　[{colored("0;95", str(self.mention))}]　{str(self.sentence_post)}'

	def __repr__(self):
		return f'{repr(self.sentence_pre)}　[{colored("0;95", repr(self.mention))}]　{repr(self.sentence_post)}'

	def __txtstr__(self):
		return f'{txtstr(self.sentence_pre)}　[{colored("0;95", txtstr(self.mention))}]　{txtstr(self.sentence_post)}'

	def __roledstr__(self):
		return f'{roledstr(self.sentence_pre)}　[{colored("0;95", roledstr(self.mention))}]　{roledstr(self.sentence_post)}'

	def __hash__(self):
		return hash(ids)

	@property
	def article(self):
		""":class:`.Article`: the article containing this mention."""
		return self.__article

	@property
	def sentence(self):
		""":class:`.WsWords`: the sentence containing this mention."""
		return self.article[self.__sid]

	@property
	def sentence_pre(self):
		""":class:`.WsWords`: the words before this mention in the sentence."""
		return self.sentence[self.slice_pre]

	@property
	def sentence_post(self):
		""":class:`.WsWords`: the words after this mention in the sentence."""
		return self.sentence[self.slice_post]

	@property
	def mention(self):
		""":class:`.WsWords`: this mention."""
		return self.sentence[self.slice]

	@property
	def ids(self):
		"""tuple: the tuple of article ID, sentence ID, and mention ID."""
		return (self.aid, self.sid, self.mid,)

	@property
	def aid(self):
		"""str: the article ID."""
		return self.__article.aid

	@property
	def sid(self):
		"""int: the sentence ID (the sentence index in the article)."""
		return self.__sid

	@property
	def mid(self):
		"""int: the mention ID (the mention index in the sentence)."""
		return self.__mid

	@property
	def start_idx(self):
		"""int: the starting index of the mention in the sentence."""
		return self.__start

	@property
	def end_idx(self):
		"""int: the ending index of the mention in the sentence."""
		return self.__end

	@property
	def last_idx(self):
		"""int: the index of the last word of the mention in the sentence."""
		return self.__end-1

	@property
	def mid(self):
		"""int: the mention ID (the mention index in the sentence)."""
		return self.__mid

	@property
	def slice(self):
		"""slice: the slice index of this mention in the sentence."""
		return slice(self.__start, self.__end)

	@property
	def slice_pre(self):
		"""slice: the slice index of the words before this mention in the sentence."""
		return slice(None, self.__start)

	@property
	def slice_post(self):
		"""slice: the slice index of the words after this mention in the sentence."""
		return slice(self.__end, None)

	@property
	def pid(self):
		"""str: the product ID."""
		return self.__pid

	@property
	def gid(self):
		"""str: the golden product ID."""
		return self.__gid

	@property
	def rule(self):
		"""str: the rule for the product ID."""
		return self.__rule

	@property
	def head_ws(self):
		""":class:`.WsWords`: the word-segmented head word."""
		return self.sentence[self.__mid]

	@property
	def head(self):
		"""str: the head word."""
		return self.head_txt

	@property
	def head_txt(self):
		"""str: the head word."""
		return self.sentence.txts[self.__mid]

	@property
	def head_tag(self):
		"""str: the head post-tag."""
		return self.sentence.tags[self.__mid]

	@property
	def head_role(self):
		"""str: the head role."""
		return self.sentence.roles[self.__mid]

	@property
	def attrs(self):
		"""The xml attributes."""
		return dict(self.__kwargs, 'sid': self.__sid, 'mid': self.__mid, 'pid': self.__pid, 'gid': self.__gid, 'rule': self.__rule)

	@property
	def start_xml(self):
		"""str: the starting XML tag."""
		return f'<product ' + ' '.join(f'{k}="{v}"' for k, v in self.attrs) + '>'

	def start_xml_(self, **kwargs):
		"""str: the starting XML tag with custom tags."""
		attrs = self.attrs
		attrs.update(kwargs)
		return f'<product ' + ' '.join(f'{k}="{v}"' for k, v in attrs) + '>'

	@property
	def end_xml(self):
		"""str: the ending XML tag."""
		return f'</product>'

	@property
	def json(self):
		"""Conver to json."""
		return json.dumps(self.attrs)

	def set_pid(self, pid):
		"""Sets the product ID."""
		self.__pid = pid

	def set_gid(self, gid):
		"""Sets the golden product ID."""
		self.__gid = gid

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
	"""

	def __init__(self, file_path, article):
		super().__init__()

		with open(file_path) as fin:
			self.__data = [Mention(article, **json.loads(line)) for line in fin]

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
		return hash(self.aid)

	@property
	def article(self):
		""":class:`.Article`: the article containing this mention."""
		return self.__article

	@property
	def aid(self):
		"""str: the article ID (with leading author name and underscore)."""
		return self.__article.aid

	@property
	def path(self):
		"""str: the related file path."""
		return self.__path

	def save(self, file_path):
		"""Save the mention bundle to json file."""
		os.makedirs(os.path.dirname(file_path), exist_ok=True)
		printr(f'Writing {os.path.relpath(file_path)}')
		with open(file_path, 'w') as fout:
			for mention in self:
				fout.write(mention.json+'\n')


class MentionBundleSet(collections.abc.Collection):
	"""The set of mention bundles.

	* Item: mention bundle (:class:`.MentionBundle`)

	Args:
		article_root (str):                 the path to the folder containing word segmented article files.
		mention_root (str):                 the path to the folder containing mention files.
		article_set (:class:`.ArticleSet`): the set of articles.
	"""

	def __init__(self, article_root, mention_root, article_set):
		super().__init__()
		n = str(len(article_set))
		self.__data = [self.__mention_bundle(article, article_root, mention_root, i, n) for i, article in enumerate(article_set)]
		self.__path = mention_root
		print()

	@staticmethod
	def __mention_bundle(article, article_root, mention_root, i, n):
		file_path = transform_path(article.path, article_root, mention_root, '.json')
		printr(f'{i+1:0{len(n)}}/{n}\tReading {file_path}')
		return MentionBundle(file_path, article)

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


class Id2MentionBundle(collections.abc.Mapping):
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
		return iter(self.__key.keys())

	def __len__(self):
		return len(self.__data)


class Head2MentionList(collections.abc.Mapping):
	"""The dictionary maps head word to mention object list.

	* Key:  mention head word (str).
	* Item: :class:`.ReadOnlyList` of mention object (:class:`.Mention`).

	Args:
		mention_set (:class:`.MentionSet`): the mention set.
	"""

	def __init__(self, mention_set):
		super().__init__()
		self.__data = dict()

		mention_dict = dict()
		for mention in mention_set:
			if mention.head not in mention_dict:
				mention_dict[mention.head] = [mention]
			else:
				mention_dict[mention.head] += [mention]

		for head, mention_set in mention_dict.items():
			self.__data[head] = ReadOnlyList(mention_set)

		self.__empty_collection = ReadOnlyList()

	def __contains__(self, key):
		return key in self.__data

	def __getitem__(self, key):
		return self.__data.get(key, self.__empty_collection)

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)
