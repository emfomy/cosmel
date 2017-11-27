#!/usr/bin/env python3
# -*- coding:utf-8 -*-

## @package t_exactMatch
#  t exact match.

import os
import pickle
import re

from IPython import embed
from ProductsRepo import ProductsRepo

## New article class.
class new_Article(object):

	## Constructor.
	def __init__(self, title, url, author, aid, sentences):
		super(new_Article, self).__init__()

		## title.
		self.title = title

		## url.
		self.url = url

		## author.
		self.author = author

		## article ID.
		self.aid = aid

		## list of sentences.
		self.sentences = []
		for i, c in enumerate(sentences):
			self.sentences.append(new_Sentence(aid, i, c))

		## list of products.
		self.products = [] # pind

		## product ID status.
		self.pid_status = []

		pass

	## Cast to string
	def __str__(self):
		s = '{}_{}, sentence[0]{}'.format(self.author, self.aid, self.sentences[0])
		return s

## New sentence class.
class new_Sentence(object):

	## Constructor.
	def __init__(self, aid, line_id, content):
		super(new_Sentence, self).__init__()

		## Article ID.
		self.aid = aid

		## Line ID.
		self.line_id = line_id

		## Content.
		self.content = content

		## list of contect segments.
		self.content_seg = [w.strip() for w in content.split('　')]

		## labeled content.
		#  @todo ???.
		self.label_content = ''

		## list of products.
		self.products = [] # pind

	## Update content segments.
	def update_content_seg(self, new_content):
		self.content_seg = [w.strip() for w in new_content.split('　')]

	## Replace labeled content.
	def replace_label_content(self, *args):
		if self.label_content == "":
			self.label_content = self.content
		self.label_content = self.label_content.replace(*args)

	## Cast to string.
	def __str__(self):
		s = '({}, {})-{}'.format(self.aid, self.line_id, self.content)
		return s

## New article processor class.
class new_ArticleProcessor(object):

	## Constructor.
	def __init__(self, articles, product_repo, complete_product_ws, last_word_set, product_ws):
		super(new_ArticleProcessor, self).__init__()

		## list of articles.
		self.articles = articles

		## product list database.
		self.product_repo = product_repo

		## word segmented product
		#  @todo ???
		self.product_ws = product_ws

		## word segmented complete product
		#  @todo ???
		self.complete_product_ws = complete_product_ws

		## set of last words
		self.last_word_set = last_word_set

	## Process all articles.
	def process_all_articles(self):
		for a in self.articles:
			print('   {}'.format(a.aid))
			previous_products = []
			for s in a.sentences:
				self.replace_product(s)
				self.replace_brand(s)
				self.decision_tree(s, a, previous_products)
				pass

	## Replace product.
	#  Replace all word with (N_product) to segemented words.
	def replace_product(self, sentence):
		for p in self.product_ws:
			sentence.content = sentence.content.replace(p, self.product_ws[p])
		sentence.update_content_seg(sentence.content)

	## Replace brand.
	#  Replace brand alias and its pos-tagging to (N_brand).
	def replace_brand(self, sentence):
		for b in self.product_repo.all_brand_set:
			b_ = re.sub(r'\W', '', b, re.IGNORECASE)
			for word in sentence.content_seg:
				if b_ in word and '(N_Cproduct)' not in word:
					sentence.content = sentence.content.replace(word, b+'(N_brand)')
		sentence.update_content_seg(sentence.content)

	## Tag using decision tree
	def decision_tree(self, sentence, article, previous_products):
		max_product_length = 12
		idx = 0;
		while idx < len(sentence.content_seg):
			word = sentence.content_seg[idx]
			if '(N_Cproduct)' in word:
				pid = self.product_repo.complete_product_to_pind[word.replace('(N_Cproduct)', '')]
				sentence.content_seg[idx] = '<pid_E="{}", gid="">{}</pid_E>'.format(pid, self.complete_product_ws[word])
				sentence.products.append(pid)
				article.products.append(pid)
				if pid in previous_products:
					previous_products.remove(pid)
				previous_products.append(pid)
			elif '(N_brand)' in word:
				# list of heads
				head_idxs = []
				for i in range(idx+1, min(idx+max_product_length-1, len(sentence.content_seg))):
					current_word = sentence.content_seg[i]
					if '(N_Cproduct)' in current_word or '(N_brand)' in current_word:
						break
					if current_word in self.last_word_set:
						head_idxs.append(i)

				# Rule 1
				passed, idx = self.check_rule(self.check_rule1, sentence.content_seg, word, idx, head_idxs, previous_products)
				if passed:
					break

				# Rule 2
				passed, idx = self.check_rule(self.check_rule2, sentence.content_seg, word, idx, head_idxs, previous_products)
				if passed:
					break

				# Rule 3
				passed, idx = self.check_rule(self.check_rule3, sentence.content_seg, word, idx, head_idxs, previous_products)
				if passed:
					break

				# Else
				passed, idx = self.check_rule(self.check_rule_else, sentence.content_seg, word, idx, head_idxs, previous_products)
				if passed:
					break

			idx = idx+1;

	## Check if word match brand of pid
	def check_word_match_brand_by_pid(self, word, pid):
		w = word.replace('(N_brand)', '')
		brands = self.product_repo.pind_to_complete_product[pid][1][0]
		b_en = brands[1]
		if len(brands) > 2:
			b_ch = brands[2]
		else:
			b_ch = ''
		return w == b_en or w == b_ch or w == b_ch+b_en or w == b_en+b_ch

	## Check a rule.
	#  @return the modified brand_idx.
	#  @return @t True/False if the rule is passed/failed.
	def check_rule(self, rule, content_seg, word, brand_idx, head_idxs, previous_products):
		for head_idx in head_idxs:
			ret = rule(content_seg, brand_idx, head_idx, previous_products)
			pid  = ret[0]
			kind = ret[1]
			if pid != None:
				content_seg[brand_idx]      = '<pid_D="{}", rule="{}", gid="">{}'.format(pid, kind, word)
				content_seg[head_idx] = '{}</pid_D>'.format(content_seg[head_idx])
				return True, head_idx
		return False, brand_idx

	## Check rule 1.
	#  Check if mention is subset of previous product.
	def check_rule1(self, content_seg, brand_idx, head_idx, previous_products):
		for pid in previous_products[::-1]:
			if self.check_word_match_brand_by_pid(content_seg[brand_idx], pid):
				product = self.product_repo.pind_to_complete_product_seg[pid]
				product = [w.strip() for w in product.split('　')]
				if content_seg[head_idx] == product[-1] and head_idx > brand_idx+1 and set(content_seg[brand_idx+1:head_idx]) <= set(product):
					return [str(pid), '1a']
		return [None, '']

	## Check rule 2.
	#  Check if mention has leading "這(Nep)"
	def check_rule2(self, content_seg, brand_idx, head_idx, previous_products):
		for pid in previous_products[::-1]:
			if '這(Nep)' in content_seg[max(brand_idx-5, 0):max(brand_idx-1, 0)]:
				if self.check_word_match_brand_by_pid(content_seg[brand_idx], pid):
					product = self.product_repo.pind_to_complete_product_seg[pid]
					product = [w.strip() for w in product.split('　')]
					if content_seg[head_idx] == product[-1]:
						return [str(pid), '2a']
				else:
					return ['OSP', '2b']
		return [None, '']

	## Check rule 3.
	#  Check if mention has leading "一Nf"
	def check_rule3(self, content_seg, brand_idx, head_idx, previous_products):
		for pid in previous_products[::-1]:
			if '一' in content_seg[max(brand_idx-2, 0)] and '(Nf)' in content_seg[max(brand_idx-1, 0)]:
				if '另' in content_seg[max(brand_idx-3, 0)] or '另外' in content_seg[max(brand_idx-3, 0)]:
					return ['OSP', '3a']
				elif self.check_word_match_brand_by_pid(content_seg[brand_idx], pid):
					product = self.product_repo.pind_to_complete_product_seg[pid]
					product = [w.strip() for w in product.split('　')]
					if content_seg[head_idx] == product[-1]:
						return [str(pid), '3b']
				else:
					return ['OSP', '3c']
		return [None, '']

	## Check rule (otherwise).
	def check_rule_else(self, content_seg, brand_idx, head_idx, previous_products):
		return ['GP', 'else']

	## Write results to file.
	def write_result(self, output_dir):
		if not os.path.exists(output_dir):
			os.makedirs(output_dir)

		for a in self.articles:
			output_path = os.path.join(output_dir, '{}_{}.txt'.format(a.author, a.aid))
			with open(output_path,'w',encoding='utf-8') as fout:
				for s in a.sentences:
					# if s.label_content:
					# 	fout.write(s.label_content)
					# else:
					# 	fout.write(s.content)
					fout.write('　'.join(s.content_seg))
					fout.write('\n')

## Load word segmented products from file.
def load_product_ws(ori_file, ws_file):
	product_ws_dict = {}
	product = []
	product_ws = []

	product = [line.replace('\tN_product', '(N_product)').strip() for line in open(ori_file, 'r', encoding='utf-8').readlines()]
	product_ws = [line.strip() for line in open(ws_file, 'r', encoding='utf-8').readlines()]

	# print(len(product), len(product_ws), len(product_ws_dict))

	duplicated = []
	for idx in range(len(product)):
		if product[idx] in product_ws_dict:
			duplicated.append(product[idx])
			# print('product: {}, ws: {}'.format(product[idx], product_ws[idx]))
		product_ws_dict[product[idx]] = product_ws[idx]


	# print(len(product_ws_dict))

	return product_ws_dict

## Load word segmented complete brands and products from file.
def load_complete_brand_n_product_ws(ori_file, ws_file, styleMe_data):
	product_ws = {}
	complete_product = []
	complete_product_ws = []

	complete_product = [line.replace('\tN_Cproduct', '(N_Cproduct)').strip() for line in open(ori_file, 'r', encoding='utf-8').readlines()]
	complete_product_ws = [line.strip() for line in open(ws_file, 'r', encoding='utf-8').readlines()]

	# styleMe_data.complete_product_to_pind
	# styleMe_data.pind_to_complete_product

	# print(len(complete_product), len(complete_product_ws), len(product_ws))

	duplicated = []
	for idx in range(len(complete_product)):

		if complete_product[idx] in product_ws:
			duplicated.append(complete_product[idx])
			# print('complete: {}, ws: {}'.format(complete_product[idx], complete_product_ws[idx]))
		product_ws[complete_product[idx]] = complete_product_ws[idx]

	## duplicated: 14896-14827=69
	## remove duplicated -> complete_product # 14758
	# print(len(product_ws))
	for ele in duplicated:
		del product_ws[ele]

	last_word = []

	for pid in styleMe_data.pind_to_complete_product:
		# embed()
		# print(pid, styleMe_data.pind_to_complete_product[pid])
		complete_product = styleMe_data.pind_to_complete_product[pid][2][0][0]
		# print('complete_product:{}'.format(complete_product))
		if complete_product+'(N_Cproduct)' in product_ws:
			# print('123')
			c_ws = product_ws[complete_product+'(N_Cproduct)']
			styleMe_data.pind_to_complete_product[pid].append(c_ws.split('　')[-1])
			last_word.append(c_ws.split('　')[-1])
			# print(styleMe_data.pind_to_complete_product[pid])

	return product_ws, set(last_word)

## Load all articles from file.
def load_all_articles(inpath):
	new_article = []

	file_dir = sorted(os.listdir(inpath))
	print(file_dir)
	for current_dir in file_dir:
		article_part = []
		filelist = os.listdir(inpath+'/'+current_dir)
		# print(filelist)
		for f in filelist:
			article = ''
			print('path:', os.path.join(inpath+'/'+current_dir, f))
			with open(os.path.join(inpath+'/'+current_dir, f), 'r', encoding='utf-8') as fin:
				line = fin.readline()
				url_idx = line.find('http://')

				title = ''.join(w.replace('('+w.split('(')[-1],'').replace('\n','') for w in line[:url_idx].replace(',(COMMACATEGORY)', '').strip() if w != '')
				url = ''.join(w.replace('('+w.split('(')[-1],'').replace('\n','') for w in line[url_idx:] if w != '')

				contents = fin.readlines()

				a = new_Article(title, url, f.split('_')[0], f.split('_')[1].replace('.txt.tag', ''), contents)
				article_part.append(a)

		new_article.append(article_part)

################################################################################################################################
		break
################################################################################################################################

	return new_article

## Test function.
def test():
	ori_file = './resources/myLexicon/all_product.txt'
	ws_file = './resources/myLexicon/all_product.txt.tag'
	product_ws = load_product_ws(ori_file, ws_file)

## Main function.
def main():

	styleMe_data = ProductsRepo('./resources//StyleMe.csv')

	ori_file = './resources/myLexicon/complete_brands_product.txt'
	ws_file = './resources/myLexicon/complete_brands_product.txt.tag'
	complete_product_ws, last_word = load_complete_brand_n_product_ws(ori_file, ws_file, styleMe_data)

	ori_file = './resources/myLexicon/all_product.txt'
	ws_file = './resources/myLexicon/all_product.txt.tag'
	product_ws = load_product_ws(ori_file, ws_file)

	fileDir = './resources/ws_articles_no_space'
	fileParts = os.listdir(fileDir)

	new_article_parts = load_all_articles(fileDir)

	for idx, new_article in enumerate(new_article_parts):
		print('current_part: part-00{:03d}'.format(idx))
		processor = new_ArticleProcessor(new_article, styleMe_data, complete_product_ws, last_word, product_ws)
		processor.process_all_articles()
################################################################################################################################
		#processor.write_result('./resources/20171116_label_xml_data/part-00{:03d}'.format(idx))
		processor.write_result('./output/label_xml_data/part-00{:03d}'.format(idx))
################################################################################################################################


## Start.
if __name__=='__main__':
	main()
	# test()
