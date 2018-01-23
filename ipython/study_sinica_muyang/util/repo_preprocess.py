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
import sys

os.chdir(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.abspath('.'))
from styleme import *

class RawData:

	def __init__(self, row):
		self.p_id    = row['編號']
		self.b_name  = row['品牌']
		self.p_name  = row['中文品名']
		self.p_descr = row['中文簡介']

		if self.b_name == '80': self.b_name = '080'
		if self.b_name == 'babaria 西班牙babaria': self.b_name = '西班牙Babaria'

		if self.p_id == '7750':  self.p_name = '巴黎時尚伸展台高級訂製濃翹美睫膏'
		if self.p_id == '11449': self.p_name = '魚子高效活氧亮白精華液'
		if self.p_id == '13315': self.p_name = '保濕修復膠囊面膜a'
		if self.p_id == '13324': self.p_name = '保濕舒緩膠囊面膜b'
		if self.p_id == '13336': self.p_name = '緊緻抗皺膠囊面膜e'
		if self.p_id == '13342': self.p_name = '再生煥膚膠囊面膜d'
		if self.p_id == '13345': self.p_name = '瞬效亮白膠囊面膜c'


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

	def __contains__(self, key):
		return self.__keytransform__(key) in self.__data

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
				print(f'Combine {self.__data[v]} and {aliases}')
				aliases.update(self.__data[v])
		if key:
			for v in brand_alias(key):
				if v in self.__data:
					print(f'Combine {self.__data[v]} and {aliases}')
					aliases.update(self.__data[v])
		for v in aliases:
			self.__data[v] = aliases

	def save_txt(self, txt_path):
		"""Save to text file."""
		os.makedirs(os.path.dirname(txt_path), exist_ok=True)
		with open(txt_path, 'w') as fout:
			for v in self.list:
				fout.write('\t'.join(v) + '\n')
		print(f'Saved {len(self.set)} brands into "{txt_path}"')

	def save_lex(self, lex_path):
		"""Save to lexicon file."""
		os.makedirs(os.path.dirname(lex_path), exist_ok=True)
		with open(lex_path, 'w') as fout:
			for k in sorted(self):
				fout.write(k + '\tN_Brand\n')
			print(f'Saved {len(self)} brands into "{lex_path}"')


class RawProduct:
	"""The product detail."""

	def __init__(self, data):
		self.p_id    = data.p_id
		self.p_descr = prune_string(data.p_descr.replace('\n', ''))


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

	def __contains__(self, key):
		return self.__keytransform__(key) in self.__data

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
			name = re.sub(rf'\A{v}', '', name).strip().strip('□')
		for v in brand:
			name = re.sub(rf'\A{v}', '', name).strip().strip('□')
		name = re.sub(r'\Ax□', '', name).strip().strip('□')
		return (brand, name)

	def update(self, data):
		"""Add ``data`` to the dictionary. Skiped if already exists."""
		key = (data.b_name, data.p_name)
		if key in self:
			print(f'Conflicted product ({self[key].p_id:>5} / {data.p_id:>5}) {self.__keytransform__(key)}')
			return
		if data.p_id in self.__ids:
			raise Exception(f'Conflicted product {data.p_id}')
		self[key] = RawProduct(data)
		self.__ids.add(data.p_id)

	def save_txt(self, txt_path):
		"""Save to text file."""
		os.makedirs(os.path.dirname(txt_path), exist_ok=True)
		with open(txt_path, 'w') as fout:
			for k, v in self.items():
				fout.write('\t'.join([v.p_id, k[0].list[-1], k[1]]) + '\n')
			print(f'Saved {len(self)} products into "{txt_path}"')

	def save_lex(self, lex_path):
		"""Save to lexicon file."""
		os.makedirs(os.path.dirname(lex_path), exist_ok=True)
		with open(lex_path, 'w') as fout:
			for k in self:
				fout.write(k[1] + '\tN_Product\n')
			print(f'Saved {len(self)} products into "{lex_path}"')

	def save_descr(self, file_path):
		"""Save description to file."""
		os.makedirs(os.path.dirname(file_path), exist_ok=True)
		with open(file_path, 'w') as fout:
			for _, v in self.items():
				if v.p_descr:
					fout.write('\t'.join([v.p_id, v.p_descr]) + '\n')
			print(f'Saved {len(self)} descriptions into "{file_path}"')

	def save_lex_c(self, lex_path):
		"""Save compute products to lexicon file."""
		os.makedirs(os.path.dirname(lex_path), exist_ok=True)
		with open(lex_path, 'w') as fout:
			i = 0
			for k in self:
				for b in k[0]:
					fout.write(prune_string(b + '□' + k[1]) + '\tN_CProduct\n')
					i += 1
			print(f'Saved {i} complete products into "{lex_path}"')


def load_csv(csv_path):
	"""Load data from CSV file.

	Load columns 編號\*, 品牌\*, 中文品名\*, 品項, 產品別名 (\*: reqired).

	Args:
		csv_path (str): the file path of the CSV file.

	Returns:
		The raw product data.
	"""
	with open(csv_path) as fin:
		data = list()
		for row in csv.DictReader(fin):

			if not row['編號'] or not row['品牌'] or not row['中文品名'] or \
					'測試' in row['品牌'] or '測試' in row['中文品名'] or \
					'test' in row['品牌'].lower() or 'test' in row['中文品名'].lower() or \
					not check_contain_chinese(row['中文品名']):
				printr(f'''Skip product {row['編號']}''')
				continue

			data.append(RawData(row))

		print(f'Loaded {len(data)} products form "{csv_path}"')

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
		raise Exception(f'Empty brand name "{full_name}"')
	return aliases


if __name__ == '__main__':

	saved_brand         = True
	saved_product       = True
	saved_descri        = True
	copied_head_lex     = True
	segmented_product   = True
	segmented_descr     = True
	copied_product_head = True

	saved_product_head  = True

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

	if not saved_brand:
		brands.save_txt(repo_path+'/brands.txt')
		brands.save_lex(repo_path+'/brands.lex')

	# Process Product
	products = RawProductDict(data, brands)
	if not saved_product:
		products.save_txt(repo_path+'/products.txt')
		products.save_lex(repo_path+'/products.lex')
		# products.save_clex(repo_path+'/cproducts.lex')

	# Save Description
	if not saved_descri:
		products.save_descr(repo_path+'/products.descr')

	if not copied_head_lex:
		# Copy Files
		shutil.copyfile(etc_path+'/core.lex', repo_path+'/core.lex')
		shutil.copyfile(etc_path+'/infix.lex', repo_path+'/infix.lex')

		# Process Head Lexicon
		with open(etc_path+'/heads.txt') as fin, open(repo_path+'/heads.lex', 'w') as fout:
			for line in fin:
				fout.write(line.strip() + '	N_Head\n')
		with open(etc_path+'/jomalone.txt') as fin, open(repo_path+'/jomalone.lex', 'w') as fout:
			for line in fin:
				fout.write(line.strip() + '	N_Head\n')

	# Word Segment
	if not segmented_product or not segmented_descr:
		ws = WordSegment(etc_path+'/for_product.ini', \
				[repo_path+'/core.lex', repo_path+'/brands.lex', repo_path+'/heads.lex', repo_path+'/jomalone.lex'], \
				[repo_path+'/infix.lex'])

	# Word Segment Product
	if not segmented_product:
		with open(repo_path+'/products.lex') as fin, open(tmp_path+'/products.lex', 'w', encoding='big5') as fout:
			fout.write(re.sub(r'	N_Product', '', fin.read(), flags=re.MULTILINE))
		ws(tmp_path+'/products.lex', tmp_path+'/products.tag')
		ws.replace(tmp_path+'/products.tag', repo_path+'/products.tag')

	# Word Segment Description
	if not segmented_descr:
		with open(repo_path+'/products.descr') as fin, open(tmp_path+'/products.descr', 'w', encoding='big5') as fout:
			fout.write(re.sub(r'(\A|(?<=\n)).*\t', '', fin.read(), flags=re.MULTILINE))
		ws(tmp_path+'/products.descr', tmp_path+'/products.descr.tag')
		ws.replace(tmp_path+'/products.descr.tag', repo_path+'/products.descr.tag')

	if not copied_product_head:
		# Copy Files
		shutil.copyfile(etc_path+'/products.head', repo_path+'/products.head')

	if not saved_product_head:
		# Grep Head
		with open(repo_path+'/products.tag') as fin, open(repo_path+'/products.head', 'w') as fout:
			for line in fin:
				sentence = WsWords(line.strip().split('\t')[0])
				if '□' in sentence.txts:
					raise Exception(f'□(SP): "{sentence}"')
				heads = list()
				if 'N_Head' in sentence.tags:
					for i, post in enumerate(sentence.tags):
						if post == 'N_Head':
							heads.append(str(sentence.txts[i]))
				if len(heads) == 0:
					print(f'No Head: "{sentence}"')
				fout.write('\t'.join(heads) + '\n')

		print(f'''Saved product heads into "{repo_path+'/products.head'}"''')

	# Check Head
	heads = {}
	with open(repo_path+'/products.head') as fin:
		for line in fin:
			p_id, head = line.strip().split('\t')
			if p_id in heads:
				raise Exception(f'Conflicted product head {p_id} "{head}"')
			heads[p_id] = head

	with open(repo_path+'/products.txt') as fin_txt, open(repo_path+'/products.tag') as fin_tag:
		for text, line in zip(fin_txt, fin_tag):
			p_id = text.strip().split('\t')[0]
			sentence = WsWords(line.strip().split('\t')[0])
			if '□' in sentence.txts:
				raise Exception(f'□(SP): "{sentence}"')

			if p_id not in heads:
				print(f'No Head (None): {p_id} "{sentence}"')
			elif heads[p_id] not in sentence.txts:
				print('No Head ({heads[p_id]}): {p_id} "{sentence}"')

	pass
