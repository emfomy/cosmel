#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import collections.abc
import csv
import os
import shutil

from styleme import *


class RawData:

	def __init__(self, p_id, b_name, p_name, p_aliases):
		self.p_id      = p_id
		self.b_name    = b_name
		self.p_name    = p_name
		self.p_aliases = p_aliases


class RawBrand(collections.abc.Collection):
	"""The brand alias collection.

	Attributes:
		list (list): the sorted list of brand aliases.
	"""

	def __init__(self, *args, **kwargs):
		super().__init__()
		self.__data = set()
		self.update(set(*args, **kwargs))

	def __contains__(self, item):
		return item in self.__data

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def __str__(self):
		return str(self.list)

	def __repr__(self):
		return str(self)

	@property
	def list(self):
		return sorted(self)

	def update(self, *args, **kwargs):
		for item in set(*args, **kwargs):
			self.__data.add(item)


class RawBrandDict(collections.abc.Mapping):
	"""The dictionary that maps brand names to all its aliases.

	Attributes:
		set  (set of sets):   the set of brand alias sets.
		list (list of lists): the sorted lists of brand alias lists.
	"""

	def __init__(self, raw_data):
		super().__init__()
		self.__data = dict()
		for v in set([v.b_name for v in raw_data]):
			self.update(v)

	def __contains__(self, item):
		return item in self.__data

	def __getitem__(self, key):
		return self.__data[self.__keytransform__(key)]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def __keytransform__(self, key):
		return brand_alias(key).pop()

	@property
	def set(self):
		return set(self.values())

	@property
	def list(self):
		return sorted([a.list for a in self.set])

	def update(self, name, key=None):
		"""Add ``name`` to the dictionary. Merges aliases if already existed.

		Args:
			key (str): if not `None`, merges ``name`` with ``key``.
		"""
		aliases = RawBrand(brand_alias(name))
		for v in set(aliases):
			if v in self.__data:
				print('Combine {} and {}'.format(self.__data[v], aliases))
				aliases.update(self.__data[v])
		if key:
			for v in brand_alias(key):
				if v in self.__data:
					print('Combine {} and {}'.format(self.__data[v], aliases))
					aliases.update(self.__data[v])
		for v in aliases:
			self.__data[v] = aliases

	def save_txt(self, txt_path):
		"""Save to text file."""
		os.makedirs(os.path.dirname(txt_path), exist_ok=True)
		with open(txt_path, 'w') as fout:
			for v in self.list:
				fout.write('\t'.join(v) + '\n')
		print('Saved {} brands into "{}"'.format(len(self.set), txt_path))

	def save_lex(self, lex_path):
		"""Save to lexicon file."""
		os.makedirs(os.path.dirname(lex_path), exist_ok=True)
		with open(lex_path, 'w') as fout:
			for k in sorted(self):
				fout.write(k + '\tN_Brand\n')
			print('Saved {} brands into "{}"'.format(len(self), lex_path))


class RawProduct:
	"""The product detail."""

	def __init__(self, data):
		self.p_id      = data.p_id
		self.p_aliases = data.p_aliases


class RawProductDict(collections.abc.Mapping):
	"""The dictionary that maps (brand name, product name) to product.
	"""

	def __init__(self, raw_data, brands):
		super().__init__()
		self.__brand_set = brands
		self.__data = dict()
		self.__ids = set()
		for v in raw_data:
			self.update(v)

	def __contains__(self, item):
		return item in self.__data

	def __getitem__(self, key):
		return self.__data[self.__keytransform__(key)]

	def __setitem__(self, key, value):
		self.__data[self.__keytransform__(key)] = value

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def __keytransform__(self, key):
		brand = key[0] if type(key[0]) == RawBrand else self.__brand_set[key[0]]
		name = prune_string(key[1])
		for v in brand:
			name = re.sub(r'\A{}'.format(v), '', name).strip().strip('□')
		for v in brand:
			name = re.sub(r'\A{}'.format(v), '', name).strip().strip('□')
		name = re.sub(r'\Ax□', '', name).strip().strip('□')
		return (brand, name)

	def update(self, data):
		"""Add ``data`` to the dictionary. Skiped if already exists."""
		key = (data.b_name, data.p_name)
		if key in self:
			print('Conflicted product ({:>5} / {:>5}) {}'.format(\
				self[key].p_id, data.p_id, self.__keytransform__(key)))
			return
		if data.p_id in self.__ids:
			raise Exception('Conflicted product {}'.format(data.p_id))
		self[key] = RawProduct(data)
		self.__ids.add(data.p_id)

	def save_txt(self, txt_path):
		"""Save to text file."""
		os.makedirs(os.path.dirname(txt_path), exist_ok=True)
		with open(txt_path, 'w') as fout:
			for k, v in self.items():
				fout.write('\t'.join([v.p_id, k[0].list[-1], k[1]]) + '\n')
			print('Saved {} products into "{}"'.format(len(self), txt_path))

	def save_lex(self, lex_path):
		"""Save to lexicon file."""
		os.makedirs(os.path.dirname(lex_path), exist_ok=True)
		with open(lex_path, 'w') as fout:
			for k in self:
				fout.write(k[1] + '\tN_Product\n')
			print('Saved {} products into "{}"'.format(len(self), lex_path))

	def save_lex_c(self, lex_path):
		"""Save compute products to lexicon file."""
		os.makedirs(os.path.dirname(lex_path), exist_ok=True)
		with open(lex_path, 'w') as fout:
			i = 0
			for k in self:
				for b in k[0]:
					fout.write(prune_string(b + '□' + k[1]) + '\tN_CProduct\n')
					i += 1
			print('Saved {} complete products into "{}"'.format(i, lex_path))


def load_csv(csv_path):
	"""Load data from CSV file.

	Load columns 編號\*, 品牌\*, 中文品名\*, 品項, 產品別名 (\*: reqired).

	Args:
		csv_path (str): the file path of the CSV file.

	Returns:
		The raw product data.
	"""
	with open(csv_path) as fin:
		data = []
		for row in csv.DictReader(fin):
			p_id      = row['編號']
			b_name    = row['品牌']
			p_name    = row['中文品名']
			p_aliases = row['產品別名']

			if not p_id or not b_name or not p_name or \
					'測試' in b_name or '測試' in p_name or \
					'test' in b_name.lower() or 'test' in p_name.lower() or \
					not check_contain_chinese(p_name):
				printr('Skip product {}'.format(p_id))
				continue

			if b_name == '80': b_name = '080'
			if b_name == 'babaria 西班牙babaria': b_name = '西班牙Babaria'

			if p_id == '7750':  p_name = '巴黎時尚伸展台高級訂製濃翹美睫膏'
			if p_id == '11449': p_name = '魚子高效活氧亮白精華液'
			if p_id == '13315': p_name = '保濕修復膠囊面膜a'
			if p_id == '13324': p_name = '保濕舒緩膠囊面膜b'
			if p_id == '13336': p_name = '緊緻抗皺膠囊面膜e'
			if p_id == '13342': p_name = '再生煥膚膠囊面膜d'
			if p_id == '13345': p_name = '瞬效亮白膠囊面膜c'

			data.append(RawData(p_id=p_id, b_name=b_name, p_name=p_name, p_aliases=p_aliases))

		print('Loaded {} products form "{}"'.format(len(data), csv_path))

		return data


def brand_alias(full_name):
	"""Generate brand name alias."""
	full_name_ = prune_string(full_name)
	full_name_ = re.sub(r'([\u4e00-\u9fff])([A-za-z])', r'\1□\2', full_name_)
	full_name_ = re.sub(r'([A-za-z])([\u4e00-\u9fff])', r'\1□\2', full_name_)

	en = ''
	zh = ''
	for elem in full_name_.split('□'):
		if not elem:
			continue
		if check_contain_chinese(elem):
			zh += elem
		else:
			en += '□' + elem

	en = en.strip().strip('□')
	zh = zh.strip().strip('□')
	en2 = re.sub(r'□', r'', en)
	aliases = set([en, en2, zh])
	aliases.discard('')
	if not len(aliases):
		raise Exception('Empty brand name "{}"'.format(full_name))
	return aliases


if __name__ == '__main__':

	has_brand           = True
	has_product         = True
	has_head            = True
	is_segmented        = True
	copied_product_head = True

	has_product_head    = True

	etc_path  = 'etc'
	repo_path = 'data/repo'
	tmp_path  = 'data/tmp'

	os.makedirs(repo_path, exist_ok=True)
	os.makedirs(tmp_path,  exist_ok=True)

	# Import CSV
	csv_path = 'data/StyleMe.csv'
	data = load_csv(csv_path)

	# Process Brand
	brands = RawBrandDict(data)
	brands.update('Pink□by□Pure□Beauty', key='Pure□Beauty')
	brands.update('SK2', key='SKII')
	brands.update('SYRIO', key='義貝拉')
	brands.update('京城之霜', key='NARUKO')
	brands.update('惹我', key='FITIT&WHITIA')
	brands.update('資生堂', key='SHISEIDO')

	if not has_brand:
		brands.save_txt(repo_path+'/brands.txt')
		brands.save_lex(repo_path+'/brands.lex')

	# Process Product
	products = RawProductDict(data, brands)
	if not has_product:
		products.save_txt(repo_path+'/products.txt')
		products.save_lex(repo_path+'/products.lex')
		# products.save_clex(repo_path+'/cproducts.lex')

	if not has_head:
		# Copy Files
		shutil.copyfile(etc_path+'/core.lex', repo_path+'/core.lex')
		shutil.copyfile(etc_path+'/description.lex', repo_path+'/description.lex')

		# Process Head Lexicon
		with open(etc_path+'/heads.txt') as fin, open(repo_path+'/heads.lex', 'w') as fout:
			for line in fin:
				fout.write(line.strip() + '	N_Head\n')
		with open(etc_path+'/jomalone.txt') as fin, open(repo_path+'/jomalone.lex', 'w') as fout:
			for line in fin:
				fout.write(line.strip() + '	N_Head\n')

	if not is_segmented:
	# Word Segment
		ws = WordSegment(etc_path+'/for_product.ini', \
				[repo_path+'/core.lex', repo_path+'/brands.lex', repo_path+'/heads.lex', repo_path+'/jomalone.lex'], \
				[repo_path+'/description.lex'])

		with open(repo_path+'/products.lex') as fin, open(tmp_path+'/products.lex', 'w', encoding='big5') as fout:
			fout.write(re.sub(r'	N_Product', '', fin.read(), flags=re.MULTILINE))
		ws(tmp_path+'/products.lex', tmp_path+'/products.tag')
		ws.replace(tmp_path+'/products.tag', repo_path+'/products.tag')

	if not copied_product_head:
		# Copy Files
		shutil.copyfile(etc_path+'/products.head', repo_path+'/products.head')

	if not has_product_head:
		# Grep Head
		with open(repo_path+'/products.tag') as fin, open(repo_path+'/products.head', 'w') as fout:
			for line in fin:
				sentence = WsWords(line.strip().split('\t')[0])
				if '□' in sentence.txts:
					raise Exception('□(SP): "{}"'.format(sentence))
				heads = []
				if 'N_Head' in sentence.tags:
					for i, post in enumerate(sentence.tags):
						if post == 'N_Head':
							heads.append(str(sentence.txts[i]))
				if len(heads) == 0:
					print('No Head: "{}"'.format(sentence))
				fout.write('\t'.join(heads) + '\n')

		print('Saved product heads into "{}"'.format(repo_path+'/products.head'))

	# Check Head
	heads = {}
	with open(repo_path+'/products.head') as fin:
		for line in fin:
			p_id, head = line.strip().split('\t')
			if p_id in heads:
				raise Exception('Conflicted product head {} "{}"'.format(p_id, head))
			heads[p_id] = head

	with open(repo_path+'/products.txt') as fin_txt, open(repo_path+'/products.tag') as fin_tag:
		for text, line in zip(fin_txt, fin_tag):
			p_id = text.strip().split('\t')[0]
			sentence = WsWords(line.strip().split('\t')[0])
			if '□' in sentence.txts:
				raise Exception('□(SP): "{}"'.format(sentence))

			if p_id not in heads:
				print('No Head (None): {} "{}"'.format(p_id, sentence))
			elif heads[p_id] not in sentence.txts:
				print('No Head ({}): {} "{}"'.format(heads[p_id], p_id, sentence))

	pass
