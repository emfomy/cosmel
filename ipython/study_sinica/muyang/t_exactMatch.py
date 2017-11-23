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

		## status of product ID.
		self.pid_status = ''

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

		## label content.
		#  @todo ???.
		self.label_content = ''

		## list of products.
		self.products = [] # pind

	## Update content segments.
	def update_content_seg(self, new_content):
		self.content_seg = [w.strip() for w in new_content.split('　')]

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
			for sent in a.sentences:
				self.exact_match(sent, a)
				self.label_gid(sent, a)

		# for a in self.articles:
		# 	for sent in a.sentences:
		# 		self.dt_one(sent, a)

	## Decision tree no.1.
	def dt_one(self, sentence, article):

		if len(sentence.products)>0:
			article.pid_status = sentence.products[-1]
		for w in sentence.content_seg:
			if w in self.last_word_set:
				if article.pid_status=='': continue
				word = self.product_repo.pind_to_complete_product[article.pid_status][3]
				if w==word:
					print(sentence.content_seg, word)
					idx = sentence.content_seg.index(w)
					for i in range(10):
						if idx>=i:
							if '(N_brand)' in sentence.content_seg[idx-i]:
								brand = sentence.content_seg[idx-i]
								# print('find brand:{}, brand:{}'.format(brand, self.product_repo.pind_to_complete_product[article.pid_status][1]))
								if brand.replace('(N_brand)', '') in self.product_repo.pind_to_complete_product[article.pid_status][1][0]:
									# print('brand:{}, content:{}'.format(brand, sentence.content_seg[idx-i:idx+1]))
									span = '　'.join(w for w in sentence.content_seg[idx-i:idx+1])
									sentence.label_content = sentence.content.replace(span, '<pid_b={}, gid="">{}</pid_b>'.format(article.pid_status, span))
									sentence.products.append(article.pid_status)
									article.products.append(article.pid_status)
									# print('sent:{}, label_sent:{}'.format(sentence.content, sentence.label_content))
									# exit()
							elif '這(Nep)' in sentence.content_seg[idx-i]:
								span = '　'.join(w for w in sentence.content_seg[idx-i:idx+1])
								sentence.label_content = sentence.content.replace(span, '<pid_c={}, gid="">{}</pid_c>'.format(article.pid_status, span))
								sentence.products.append(article.pid_status)
								article.products.append(article.pid_status)

	## Add golden ID of label.
	def label_gid(self, sentence, article):
		# if not sentence.label_content=='': return
		for w in sentence.content_seg:
			if w in self.last_word_set:
				# if article.pid_status=='': continue
				# word = self.product_repo.pind_to_complete_product[article.pid_status][3]
				# if w==word:
				# 	print(sentence.content_seg, word)
				idx = sentence.content_seg.index(w)
				for i in range(idx-1, -1, -1):
					current_word = sentence.content_seg[i].replace('('+sentence.content_seg[i].split('(')[-1],'')
					if current_word in self.product_repo.all_brand_set:
						span = '　'.join(w for w in sentence.content_seg[i:idx+1])
						sentence.label_content = sentence.content.replace(span, '<gid="">{}</gid>'.format(span))
						break
						# print('sent:{}, label_sent:{}'.format(sentence.content, sentence.label_content))
					else:
						for b in self.product_repo.all_brand_set:
							if current_word == re.sub(r'\W', '', b, re.IGNORECASE):
								span = '　'.join(w for w in sentence.content_seg[i:idx+1])
								sentence.label_content = sentence.content.replace(span, '<gid="">{}</gid>'.format(span))
								break

	## Find exact matches.
	def exact_match(self, sentence, article):
		complete_product_keys = self.complete_product_ws.keys()
		for p in complete_product_keys:
			if p in sentence.content:
				pid = self.product_repo.complete_product_to_pind[p.replace('(N_Cproduct)', '')]
				sentence.label_content = sentence.content.replace(p, '<pid_a={}, gid="">{}</pid_a>'.format(pid, self.complete_product_ws[p]))
				sentence.products.append(pid)
				article.products.append(pid)
				# print('product:{}, sent:{}, label_sent:{}'.format(p, sentence.content, sentence.label_content))

		for p in self.product_ws:
			if p in sentence.content:
				sentence.content = sentence.content.replace(p, self.product_ws[p])
				sentence.update_content_seg(sentence.content)

	## Write results to file.
	def write_result(self, output_dir):
		if not os.path.exists(output_dir):
			os.makedirs(output_dir)

		for a in self.articles:
			output_path = os.path.join(output_dir, '{}_{}.txt'.format(a.author, a.aid))
			with open(output_path,'w',encoding='utf-8') as fout:
				for s in a.sentences:
					if s.label_content:
						fout.write(s.label_content)
					else:
						fout.write(s.content)
					fout.write('\n')

## Load word segmented products from file.
def load_product_ws(ori_file, ws_file):
	product_ws_dict = {}
	product = []
	product_ws = []

	product = [line.replace('\tN_product', '(N_product)').strip() for line in open(ori_file, 'r', encoding='utf-8').readlines()]
	product_ws = [line.strip() for line in open(ws_file, 'r', encoding='utf-8').readlines()]

	print(len(product), len(product_ws), len(product_ws_dict))


	duplicated = []
	for idx in range(len(product)):
		if product[idx] in product_ws_dict:
			duplicated.append(product[idx])
			# print('product: {}, ws: {}'.format(product[idx], product_ws[idx]))
		product_ws_dict[product[idx]] = product_ws[idx]


	print(len(product_ws_dict))

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

	fileDir = './resources/ws_articles_no_space/'
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