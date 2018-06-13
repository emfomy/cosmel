#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import argparse
import collections
import collections.abc
import csv
import os
import shutil
import sys

if __name__ == '__main__':
	sys.path.insert(0, os.path.abspath('.'))

from cosmel import *


def main():

	# Parse arguments
	argparser = argparse.ArgumentParser(description='CosmEL: Generate Database.')

	argparser.add_argument('-i', '--input', required=True, \
		help='load CSV from file <INPUT>')
	argparser.add_argument('-d', '--database', required=True, \
		help='save/load database from directory <DATABASE>')
	argparser.add_argument('--etc', action='store_true', \
		help='use predefined etc files (from ./etc)')

	args = argparser.parse_args()

	csv_path  = os.path.normpath(args.input)
	assert os.path.isfile(csv_path)

	repo_root = os.path.normpath(args.database)
	copy_etc  = args.etc

	print(args)

	created_empty       = False
	created_lexicon     = False
	saved_brand         = False
	saved_product       = False
	saved_descri        = False
	saved_csv           = False
	segmented_product   = False
	counted_word        = False
	segmented_descr     = False

	main_etc_root = f'etc'

	global etc_root

	etc_root  = f'{repo_root}/etc'
	tmp_root  = f'data/tmp'

	os.makedirs(repo_root, exist_ok=True)
	os.makedirs(etc_root,  exist_ok=True)
	os.makedirs(tmp_root,  exist_ok=True)

	# Copy ETC
	etc_file_list = [ \
		'etc0.py', \
		'brand0.txt', \
		'core0.lex', \
		'infix0.lex', \
		'head0.txt', \
		'compound0.txt', \
		'product.head0', \
	]
	if copy_etc:
		for file in etc_file_list:
			shutil.copyfile(f'{main_etc_root}/{file}', f'{etc_root}/{file}')
			print(f'Copied "{main_etc_root}/{file}" to "{etc_root}/{file}"')
	else:
		for file in etc_file_list:
			with open(f'{etc_root}/{file}', 'a'): pass
			print(f'Created "{etc_root}/{file}"')

	# Create Lexicon
	if not created_lexicon:

		# Process Core
		with open(etc_root+'/core0.lex') as fin, open(repo_root+'/core.lex', 'w') as fout:
			fout.write('□	SP\n\n'+fin.read())

		# Process Infix
		with open(etc_root+'/infix0.lex') as fin, open(repo_root+'/infix.lex', 'w') as fout:
			fout.write(fin.read())

		# Process Heads
		with open(etc_root+'/head0.txt') as fin, open(repo_root+'/head.txt', 'w') as fout:
			fout.write(fin.read())

		# Process Heads
		with open(etc_root+'/compound0.txt') as fin, open(repo_root+'/compound.txt', 'w') as fout:
			fout.write(fin.read())

		# Process Product Heads
		with open(etc_root+'/product.head0') as fin, open(repo_root+'/product.head', 'w') as fout:
			fout.write(fin.read())

		# Process Head Lexicons
		with open(repo_root+'/head.txt') as fin, open(repo_root+'/head.lex', 'w') as fout:
			for line in fin:
				if line.strip() == '': continue
				fout.write(line.strip().split('\t')[0] + '	Na\n')

		# Process Compound Lexicons
		with open(repo_root+'/compound.txt') as fin, open(repo_root+'/compound.lex', 'w') as fout:
			for line in fin:
				if line.strip() == '': continue
				fout.write(line.strip().split('\t')[0] + '	Nb\n')

	# Import CSV
	data = load_csv(csv_path)

	# Process Brands
	brands = RawBrandDict(data)
	with open(etc_root+'/brand0.txt') as fin:
		for line in fin:
			if line.strip() == '': continue
			bnames = line.strip().split('\t')
			for bname in bnames[1:]:
				brands.update(bname, key=bnames[0])
	if not saved_brand:
		brands.save_txt(repo_root+'/brand.txt')
		brands.save_lex(repo_root+'/brand.lex')

	# Process Products
	products = RawProductDict(data, brands)
	if not saved_product:
		products.save_txt(repo_root+'/product.txt')
		products.save_lex(repo_root+'/product.lex')

	# Save Descriptions
	if not saved_descri:
		products.save_descr(repo_root+'/product.descr')

	# Load Heads / Infixes
	head_set     = set(WordSet(repo_root+'/head.lex'))
	infix_set    = set(WordSet(repo_root+'/infix.lex'))
	compound_set = set(WordSet(repo_root+'/compound.lex'))
	for txt in (infix_set & head_set):
		print(colored('1;31', f'Conflicted infix/head ({txt})'))
	for txt in (compound_set & head_set):
		print(colored('1;31', f'Conflicted compound/head ({txt})'))
	for txt in (compound_set & infix_set):
		print(colored('1;31', f'Conflicted compound/infix ({txt})'))

	# Word-Segment Product
	if not segmented_product:
		ckipws = CkipWs(main_etc_root+'/for_product.ini', \
				[repo_root+'/core.lex', repo_root+'/brand.lex', repo_root+'/head.lex', \
					repo_root+'/infix.lex', repo_root+'/compound.lex'], [repo_root+'/compound.txt'])
		with open(repo_root+'/product.lex') as fin, open(tmp_root+'/product.lex', 'w', encoding=None) as fout:
			fout.write(re.sub(r'\t.*', '', fin.read().strip()+'\n', flags=re.MULTILINE))
		ckipws.ws_file(tmp_root+'/product.lex', tmp_root+'/product.tag')
		ckipws.replace(tmp_root+'/product.tag', repo_root+'/product.tag')

	# Load Product Heads
	product_head = dict()
	with open(repo_root+'/product.head') as fin:
		for line in fin:
			if line.strip() == '': continue
			pid, head = line.strip().split('\t')
			if pid in product_head:
				raise Exception(colored('1;31', f'Conflicted product head {pid} "{head}"'))
			product_head[pid] = head

	# Generate Product Heads
	with open(repo_root+'/product.txt') as fin_txt, open(repo_root+'/product.tag') as fin_tag, \
			open(etc_root+'/product.head0.auto', 'w') as fout:
		for txt_line, tag_line in zip(fin_txt, fin_tag):
			pid = txt_line.strip().split('\t')[0]
			sentence = WsWords(tag_line.strip().split('\t')[0])
			if pid not in product_head:
				head = sentence.txts[-1]
				for txt, tag in zip(reversed(sentence.txts), reversed(sentence.tags)):
					if tag == 'Na' or tag == 'Nb':
						head = txt
						break
				product_head[pid] = head
				fout.write(f'{pid}\t{head}\n')
				print(colored('1;31', f'No Head: {pid} "{sentence}"'))

	# Check Unexpected Space
	with open(repo_root+'/product.txt') as fin_txt, open(repo_root+'/product.tag') as fin_tag:
		for txt_line, tag_line in zip(fin_txt, fin_tag):
			pid = txt_line.strip().split('\t')[0]
			sentence = WsWords(tag_line.strip().split('\t')[0])
			for txt in sentence.txts:
				if '□' == txt:
					print(colored('1;31', f'□(SP): "{sentence}"'))
				if '□' == txt[0]:
					print(colored('1;31', f'□***: "{sentence}"'))

	# Check Unbound Tags (b)
	with open(repo_root+'/product.txt') as fin_txt, open(repo_root+'/product.tag') as fin_tag:
		for text, line in zip(fin_txt, fin_tag):
			pid = text.strip().split('\t')[0]
			sentence = WsWords(line.strip())
			if 'b' in sentence.tags:
				print(colored('1;31', f'Tag (b) ({product_head[pid]}): {pid} "{sentence}"'))

	# Check Unknown Heads
	auto_head_set = set()
	with open(repo_root+'/product.txt') as fin_txt, open(repo_root+'/product.tag') as fin_tag:
		for txt_line, tag_line in zip(fin_txt, fin_tag):
			pid = txt_line.strip().split('\t')[0]
			sentence = WsWords(tag_line.strip())
			if product_head[pid] not in head_set:
				auto_head_set.add(product_head[pid])
				print(colored('1;31', f'Unknown Head ({product_head[pid]}): {pid} "{sentence}"'))
	with open(etc_root+'/head0.txt.auto', 'w') as fout:
		for head in auto_head_set:
			fout.write(f'{head}\n')

	# Check Product Heads
	with open(repo_root+'/product.txt') as fin_txt, open(repo_root+'/product.tag') as fin_tag:
		for txt_line, tag_line in zip(fin_txt, fin_tag):
			pid = txt_line.strip().split('\t')[0]
			sentence = WsWords(tag_line.strip())

			if pid not in product_head:
				print(colored('1;31', f'No Head ({None}): {pid} "{sentence}"'))
			elif product_head[pid] not in sentence.txts:
				print(colored('1;31', f'No Head ({product_head[pid]}): {pid} "{sentence}"'))

	# Check Unused words
	with open(tmp_root+'/product.tag') as fin_product_tag, open(repo_root+'/product.head') as fin_product_head:

		for line in fin_product_tag:
			sentence = WsWords(line.strip())
			txt_set = set(sentence.txts)
			infix_set -= txt_set
			compound_set -= txt_set

		for line in fin_product_head:
			head_set.discard(line.strip().split('\t')[1])

		for txt in head_set:
			print(colored('0;33', f'Unused head ({txt})'))
		for txt in infix_set:
			print(colored('0;33', f'Unused infix ({txt})'))
		for txt in compound_set:
			print(colored('0;33', f'Unused compound ({txt})'))

	# Output Lexicon
	if not counted_word:
		infix_count = collections.OrderedDict()

		with open(etc_root+'/infix0.lex') as fin:
			for line in fin:
				if line.strip() == '': continue
				txt, tag = line.strip().split('\t')
				if txt not in infix_count:
					infix_count[txt] = collections.OrderedDict()
				if tag not in infix_count[txt]:
					infix_count[txt][tag] = 0

		with open(repo_root+'/product.tag') as fin:
			for line in fin:
				sentence = WsWords(line.strip())
				for txt, tag in sentence.zip2:
					if txt in brands or txt in head_set:
						continue
					if txt not in infix_count:
						infix_count[txt] = collections.OrderedDict()
					if tag not in infix_count[txt]:
						infix_count[txt][tag] = 1
					else:
						infix_count[txt][tag] += 1

		with open(repo_root+'/core.lex') as fin, \
				open(repo_root+'/infix.lex', 'w') as fout_lex, open(repo_root+'/infix.txt', 'w') as fout_txt:
			for line in fin:
				if line.strip() == '': continue
				txt = line.strip().split('\t')[0]
				if txt != '□':
					fout_txt.write(f'{txt}\n')

			for txt, tag_dict in infix_count.items():
				total = sum(tag_dict.values())

				for tag, count in tag_dict.items():
					if 'Neu' != tag:
						fout_lex.write(f'{txt}\t{tag}\t{count}\n')
				if total >= 2 and 'Neu' not in tag_dict:
						fout_txt.write(f'{txt}\n')

	# Word-Segment Description
	if not segmented_descr:
		ckipws = CkipWs(main_etc_root+'/for_article.ini', \
				[repo_root+'/core.lex', repo_root+'/brand.lex', repo_root+'/head.lex', \
					repo_root+'/infix.lex', repo_root+'/compound.lex'], [repo_root+'/compound.txt'])
		with open(repo_root+'/product.descr') as fin, open(tmp_root+'/product.descr', 'w', encoding=None) as fout:
			fout.write(re.sub(r'(\A|(?<=\n)).*\t', '', fin.read().strip()+'\n', flags=re.MULTILINE))
		ckipws.ws_line(tmp_root+'/product.descr', tmp_root+'/product.descr.tag')
		ckipws.replace(tmp_root+'/product.descr.tag', repo_root+'/product.descr.tag')


class RawData:

	def __init__(self, row):
		self.pid   = row['編號']
		self.bname = row['品牌']
		self.pname = row['中文品名']
		self.descr = row['中文簡介']

		global etc_root

		exec(open(etc_root+'/etc0.py').read())

		self.raw = row


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
		return sorted(sorted(self), key=len, reverse=True)

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
		for v in set([v.bname for v in raw_data]):
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
				print(colored('0;33', f'Combine {self.__data[v]} and {aliases}'))
				aliases.update(self.__data[v])
		if key:
			for v in brand_alias(key):
				if v in self.__data:
					print(colored('0;33', f'Combine {self.__data[v]} and {aliases}'))
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
				fout.write(k + '\tNb\n')
			print(f'Saved {len(self)} brands into "{lex_path}"')


class RawProduct:
	"""The product detail."""

	def __init__(self, data):
		self.pid   = data.pid
		self.descr = purge_string(data.descr.replace('\n', ''))


class RawProductDict(collections.abc.Mapping):
	"""The dictionary that maps (brand name, product name) to product.
	"""

	def __init__(self, raw_data, brands):
		super().__init__()
		self.__brand_dict = brands
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
		brand = key[0] if type(key[0]) == RawBrand else self.__brand_dict[key[0]]
		name = purge_string(key[1])
		for v in brand.list:
			name = re.sub(rf'\A{v}', '', name).strip().strip('□')
		for v in brand.list:
			name = re.sub(rf'\A{v}', '', name).strip().strip('□')
		name = re.sub(r'\Ax□', '', name).strip().strip('□')
		return (brand, name)

	def update(self, data):
		"""Add ``data`` to the dictionary. Skipped if already exists."""
		key = (data.bname, data.pname)
		if key in self:
			print(colored('0;33', f'Conflicted product ({self[key].pid:>5} / {data.pid:>5}) {self.__keytransform__(key)}'))
			return
		if data.pid in self.__ids:
			raise Exception(colored('1;31', f'Conflicted product {data.pid}'))
		self[key] = RawProduct(data)
		self.__ids.add(data.pid)

	def save_txt(self, txt_path):
		"""Save to text file."""
		os.makedirs(os.path.dirname(txt_path), exist_ok=True)
		with open(txt_path, 'w') as fout:
			for k, v in self.items():
				fout.write('\t'.join([v.pid, k[0].list[-1], k[1]]) + '\n')
			print(f'Saved {len(self)} products into "{txt_path}"')

	def save_lex(self, lex_path):
		"""Save to lexicon file."""
		os.makedirs(os.path.dirname(lex_path), exist_ok=True)
		with open(lex_path, 'w') as fout:
			for k in self:
				fout.write(k[1] + '\tNb\n')
			print(f'Saved {len(self)} products into "{lex_path}"')

	def save_descr(self, file_path):
		"""Save description to file."""
		os.makedirs(os.path.dirname(file_path), exist_ok=True)
		with open(file_path, 'w') as fout:
			for _, v in self.items():
				if v.descr:
					fout.write('\t'.join([v.pid, v.descr]) + '\n')
			print(f'Saved {len(self)} descriptions into "{file_path}"')


def load_csv(csv_path):
	"""Load data from CSV file.

	Load columns 編號*, 品牌*, 中文品名*, 品項, 產品別名 (*: required).

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
				printr(f'Skip product {row["編號"]}')
				continue

			data.append(RawData(row))

		print(f'Loaded {len(data)} products form "{csv_path}"')

		return data


def brand_alias(full_name):
	"""Generate brand name alias."""
	full_name_ = purge_string(full_name)
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
	en2 = re.sub('□', '', en)
	aliases = set([en, en2, zh])
	aliases.discard('')
	if not len(aliases):
		raise Exception(colored('1;31', f'Empty brand name "{full_name}"'))
	if '\'s' in full_name.lower():
		aliases |= brand_alias(re.sub(r'\'s\b', '', full_name.lower()))
	return aliases


if __name__ == '__main__':

	main()
	print()
	pass
