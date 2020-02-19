#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <http://muyang.pro>'
__copyright__ = 'Copyright 2017-2018'


import collections.abc
import itertools
import json
import operator
import os

from cosmel.util import *
from cosmel.corpus.article import *


class Mention:
	"""The mention class.

	Args:
		article (:class:`.Article`): the article containing this mention.
		sid     (int):               the sentence index in the aritcle.
		mid     (int):               the mention index in the sentence.
		gid     (str):               the golden product ID.
		nid     (str):               the network-predicted product ID.
		rid     (str):               the rule-labeled product ID.
		rule    (str):               the rule.
		idxs    (slice):             the indix slice of this mention.
	"""

	def __init__(self, article, sid, mid, *, gid='', nid='', rid='', rule='', **kwargs):

		super().__init__()

		self.__article = article
		self.__sid     = int(sid)
		self.__mid     = int(mid)
		self.__gid     = gid
		self.__nid     = nid
		self.__rid     = rid
		self.__rule    = rule
		self.__start   = self.__mid
		self.__end     = self.__mid+1
		self.__kwargs  = kwargs

	def __str__(self):
		return f'{str(self.sentence_pre)}　[{colored("0;95", str(self.mention))}]　{str(self.sentence_post)}'

	def __repr__(self):
		return f'{repr(self.sentence_pre)}　[{colored("0;95", repr(self.mention))}]　{repr(self.sentence_post)}'

	def __txtstr__(self):
		return f'{txtstr(self.sentence_pre)}[{colored("0;95", txtstr(self.mention))}]{txtstr(self.sentence_post)}'

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
		return self.sentence[self._slice_pre]

	def sentence_pre_(self, with_mention=True):
		""":class:`.WsWords`: the words before this mention in the sentence (with/without mention itself)."""
		return self.sentence[self._slice_pre_(with_mention)]

	@property
	def sentence_post(self):
		""":class:`.WsWords`: the words after this mention in the sentence."""
		return self.sentence[self._slice_post]

	def sentence_post_(self, with_mention=True):
		""":class:`.WsWords`: the words after this mention in the sentence (with/without mention itself)."""
		return self.sentence[self._slice_post_(with_mention)]

	@property
	def mention(self):
		""":class:`.WsWords`: this mention."""
		return self.sentence[self._slice]

	@property
	def bundle(self):
		""":class:`.MentionBundle`: the mention bundle containing this mention."""
		return self.__article.bundle

	@property
	def asmid(self):
		"""tuple: the tuple of article ID, sentence ID, and mention ID."""
		return (self.aid, self.sid, self.mid,)

	@property
	def ids(self):
		return self.asmid

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
	def _slice(self):
		"""slice: the slice index of this mention in the sentence."""
		return slice(self.__start, self.__end)

	@property
	def _slice_pre(self):
		"""slice: the slice index of the words before this mention in the sentence."""
		return slice(None, self.__start)

	def _slice_pre_(self, with_mention=True):
		"""slice: the slice index of the words before this mention in the sentence (with/without mention)."""
		return slice(None, self.__end) if with_mention else slice(None, self.__start)

	@property
	def _slice_post(self):
		"""slice: the slice index of the words after this mention in the sentence."""
		return slice(self.__end, None)

	def _slice_post_(self, with_mention=True):
		"""slice: the slice index of the words after this mention in the sentence (with/without mention)."""
		return slice(self.__start, None) if with_mention else slice(self.__end, None)

	@property
	def gid(self):
		"""str: the golden product ID."""
		return self.__gid

	@property
	def nid(self):
		"""str: the network-predicted product ID."""
		return self.__nid

	@property
	def rid(self):
		"""str: the rule-labeled product ID."""
		return self.__rid

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
		return dict(sid=self.__sid, mid=self.__mid, gid=self.__gid, nid=self.__nid, rid=self.__rid, \
				rule=self.__rule, **self.__kwargs)

	@property
	def start_xml(self):
		"""str: the starting XML tag."""
		return f'<product ' + ' '.join(f'{k}="{v}"' for k, v in self.attrs.items()) + '>'

	def start_xml_(self, **kwargs):
		"""str: the starting XML tag with custom attributes."""
		attrs = self.attrs
		attrs.update(kwargs)
		return f'<product ' + ' '.join(f'{k}="{v}"' for k, v in attrs.items()) + '>'

	@property
	def end_xml(self):
		"""str: the ending XML tag."""
		return f'</product>'

	@property
	def json(self):
		"""Convert to json."""
		return json.dumps(self.attrs)

	def set_gid(self, gid):
		"""Sets the golden product ID."""
		self.__gid = gid

	def set_nid(self, nid):
		"""Sets the network-predicted product ID."""
		self.__nid = nid

	def set_rid(self, rid):
		"""Sets the rule-labeled product ID."""
		self.__rid = rid

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
		self.__path = mention_bundles.path

	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	@property
	def path(self):
		"""str: the root path of the mentions."""
		return self.__path


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
		return '\n'.join(map(str, self.__data))

	def __repr__(self):
		return '\n'.join(map(repr, self.__data))

	def __txtstr__(self):
		return '\n'.join(map(txtstr, self.__data))

	def __roledstr__(self):
		return '\n'.join(map(roledstr, self.__data))

	def __hash__(self):
		return hash(self.aid)

	@property
	def article(self):
		""":class:`.Article`: the article of this bundle."""
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

	def __init__(self, mention_root, article_set):
		super().__init__()
		n = str(len(article_set))
		self.__data = [self.__mention_bundle(article, article_set.path, mention_root, i, n) \
				for i, article in enumerate(article_set)]
		self.__path = mention_root
		print()

	@staticmethod
	def __mention_bundle(article, article_root, mention_root, i, n):
		file_path = transform_path(article.path, article_root, mention_root, '.json')
		printr(f'{i+1:0{len(n)}}/{n}\tReading {file_path[-80:]}')
		bundle = MentionBundle(file_path, article)
		article._Article__bundle = bundle
		return bundle

	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	@property
	def path(self):
		"""str: the root path of the mentions."""
		return self.__path

	def save(self, output_root):
		"""Save all mention bundles to files."""
		n = str(len(self))
		for i, bundle in enumerate(self):
			file_path = bundle.path.replace(self.__path, output_root)
			printr(f'{i+1:0{len(n)}}/{n}\t{file_path}')
			bundle.save(file_path)
		print()


class Id2Mention(collections.abc.Mapping):
	"""The dictionary maps article ID, sentence ID, and mention ID to mention object.

	* Key:  the article ID, sentence ID, and mention ID (tuple).
	* Item: the mention object (:class:`.Mention`).

	Args:
		mention_set (:class:`.MentionSet`): the mention set.
	"""

	def __init__(self, mention_set):
		super().__init__()
		self.__data = dict((mention.asmid, mention,) for mention in mention_set)

	def __contains__(self, key):
		return key in self.__data

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)


class Id2MentionBundle(collections.abc.Mapping):
	"""The dictionary maps article ID to mention bundle.

	* Key:  the article ID (str).
	* Item: the mention bundle (:class:`.MentionBundle`).

	Args:
		id_to_article (:class:`.Id2Article`): the dictionary maps article ID to article object.
	"""

	def __init__(self, id_to_article):
		super().__init__()
		self.__data  = id_to_article

	def __contains__(self, key):
		return key in self.__data

	def __getitem__(self, key):
		return self.__data[key].bundle

	def __iter__(self):
		return iter(map(self.__data, operator.attrgetter('bundle')))

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
