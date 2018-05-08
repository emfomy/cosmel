#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import itertools

import torch

def lstm_size(module):
	return module.hidden_size * (module.bidirectional+1)

def cnn_size(module):
	return module.hidden_size

def relu(x):
	return max(x, 0)


################################################################################################################################
# Context Encoder
#

class ContextEncoder(torch.nn.Module):

	def __init__(self, meta, word_emb_module, lstm_emb_size):

		super().__init__()
		self.meta = meta

		# Set dimensions
		w2v_emb_size = word_emb_module.embedding_dim

		# Set size
		self.output_size = w2v_emb_size

		# Create modules
		self.local_encoder = LocalContextEncoder(meta, word_emb_module, lstm_emb_size)
		self.title_encoder = TitleContextEncoder(meta, word_emb_module, lstm_emb_size)
		self.docu_encoder  = DocumentEncoder(meta, word_emb_module)

		concat_size = self.local_encoder.output_size + self.title_encoder.output_size + self.docu_encoder.output_size
		self.linear = torch.nn.Linear(concat_size, self.output_size)

	def data(self, ment_list, repo, corpus):

		return \
			self.local_encoder.data(ment_list, repo, corpus) + \
			self.title_encoder.data(ment_list, repo, corpus) + \
			self.docu_encoder.data(ment_list, repo, corpus)

	def forward(self, pre_pad, post_pad, title_pad, pid_bag, brand_bag):

		local_emb = self.local_encoder(pre_pad, post_pad)
		title_emb = self.title_encoder(title_pad)
		docu_emb  = self.docu_encoder(pid_bag, brand_bag)
		text_emb  = self.linear(torch.cat((local_emb, title_emb, docu_emb), dim=1)).clamp(min=0)

		return text_emb


class LocalContextEncoder(torch.nn.Module):

	def __init__(self, meta, word_emb_module, lstm_emb_size):

		super().__init__()
		self.meta = meta

		# Set dimensions
		w2v_emb_size = word_emb_module.embedding_dim

		# Set size
		self.output_size = w2v_emb_size
		self.max_num_sentences = 5

		# Create modules
		self.word_emb  = word_emb_module

		self.pre_lstm  = torch.nn.LSTM(w2v_emb_size, lstm_emb_size, batch_first=True)
		self.post_lstm = torch.nn.LSTM(w2v_emb_size, lstm_emb_size, batch_first=True)

		self.linear = torch.nn.Linear(lstm_size(self.pre_lstm) + lstm_size(self.post_lstm), self.output_size)

	def extra_repr(self):

		return f'max_num_sentences={self.max_num_sentences}'

	def data(self, ment_list, repo, corpus):

		# Load context
		raw_pre  = [ \
				list(itertools.chain( \
						itertools.chain.from_iterable( \
								s.txts for s in mention.article[relu(mention.sid-self.max_num_sentences):mention.sid] \
						), \
						mention.sentence_pre_().txts \
				)) for mention in ment_list \
		]
		raw_post = [ \
				list(itertools.chain( \
						mention.sentence_post_().txts, \
						itertools.chain.from_iterable( \
								s.txts for s in mention.article[mention.sid+1:mention.sid+1+self.max_num_sentences] \
						) \
				)) for mention in ment_list \
		]

		# Encode
		pre_code  = self.meta.tokenizer.transform_sequences(raw_pre)
		post_code = self.meta.tokenizer.transform_sequences(raw_post)

		# Pad
		pre_pad  = self.meta.padder(pre_code,   padding='pre')
		post_pad = self.meta.padder(post_code,  padding='post')

		# Combine inputs
		pre_pad_var   = torch.from_numpy(pre_pad).long()
		post_pad_var  = torch.from_numpy(post_pad).long()

		return pre_pad_var, post_pad_var,

	def forward(self, pre_pad, post_pad):

		pre_pad_emb  = self.word_emb(pre_pad)
		post_pad_emb = self.word_emb(post_pad)

		pre_lstm0, _  = self.pre_lstm(pre_pad_emb)
		post_lstm0, _ = self.post_lstm(post_pad_emb)

		pre_lstm  = pre_lstm0[:, -1, :]
		post_lstm = post_lstm0[:, -1, :]

		local_emb = self.linear(torch.cat((pre_lstm, post_lstm), dim=1)).clamp(min=0)

		return local_emb


class TitleContextEncoder(torch.nn.Module):

	def __init__(self, meta, word_emb_module, lstm_emb_size):

		super().__init__()
		self.meta = meta

		# Set dimensions
		w2v_emb_size = word_emb_module.embedding_dim

		# Set size
		self.output_size = w2v_emb_size

		# Create modules
		self.word_emb   = word_emb_module
		self.title_lstm = torch.nn.LSTM(w2v_emb_size, lstm_emb_size, batch_first=True, bidirectional=True)
		self.linear     = torch.nn.Linear(lstm_size(self.title_lstm), self.output_size)

	def data(self, ment_list, repo, corpus):

		# Load context
		raw_title = [ \
				mention.article[0].txts for mention in ment_list \
		]

		# Encode
		title_code = self.meta.tokenizer.transform_sequences(raw_title)

		# Pad
		title_pad = self.meta.padder(title_code, padding='post')

		# Combine inputs
		title_pad_var = torch.from_numpy(title_pad).long()

		return title_pad_var,

	def forward(self, title_pad):

		title_pad_emb = self.word_emb(title_pad)
		title_lstm0, _ = self.title_lstm(title_pad_emb)
		title_lstm = title_lstm0[:, -1, :]
		title_emb = self.linear(title_lstm).clamp(min=0)

		return title_emb


class DocumentEncoder(torch.nn.Module):

	def __init__(self, meta, word_emb_module):

		super().__init__()
		self.meta = meta

		# Get dimensions
		w2v_emb_size = word_emb_module.embedding_dim
		num_label    = len(meta.p_encoder.classes_)
		num_brand    = len(meta.b_encoder.classes_)

		# Set size
		self.output_size = w2v_emb_size

		# Create modules
		self.word_emb = word_emb_module

		self.linear = torch.nn.Linear(num_label+num_brand, self.output_size)

	def data(self, ment_list, repo, corpus):

		# Load bag
		raw_pid_bag   = [set(m.pid for m in mention.bundle if m.rule == 'P_rule1') for mention in ment_list]
		raw_brand_bag = [ \
				set(repo.bname_to_brand[t[0]][0] \
						for t in itertools.chain.from_iterable(sentence.zip3 for sentence in mention.article) if t[2] == 'Brand' \
				) for mention in ment_list \
		]

		# Encode
		pid_bag   = self.meta.p_multibinarizer.transform(raw_pid_bag)
		brand_bag = self.meta.b_multibinarizer.transform(raw_brand_bag)

		# Combine inputs
		pid_bag_var   = torch.from_numpy(pid_bag).float()
		brand_bag_var = torch.from_numpy(brand_bag).float()

		return pid_bag_var, brand_bag_var,

	def forward(self, pid_bag, brand_bag):

		docu_emb = self.linear(torch.cat((pid_bag, brand_bag), dim=1)).clamp(min=0)

		return docu_emb


################################################################################################################################
# Description Encoder
#

class DescriptionEncoder(torch.nn.Module):

	def __init__(self, meta, word_emb_module, cnn_emb_size, cnn_win_size):

		super().__init__()
		self.meta = meta

		# Get dimensions
		w2v_emb_size = word_emb_module.embedding_dim

		# Set size
		self.output_size = w2v_emb_size

		# Create modules
		self.word_emb = word_emb_module

		self.conv1d = torch.nn.Conv1d(w2v_emb_size, cnn_emb_size, cnn_win_size)
		self.linear = torch.nn.Linear(cnn_emb_size, w2v_emb_size)

	def data(self, prod_list, repo, corpus):

		# Load context
		raw_desc = [product.descr_ws.txts for product in prod_list]

		# Encode
		desc_code = self.meta.tokenizer.transform_sequences(raw_desc)

		# Pad
		desc_pad = self.meta.padder(desc_code, padding='post')

		# Combine inputs
		desc_pad_var = torch.from_numpy(desc_pad).long()

		return desc_pad_var,

	def forward(self, desc_pad):

		desc_pad_emb = self.word_emb(desc_pad)
		desc_cnn     = self.conv1d(desc_pad_emb.permute(0, 2, 1))
		desc_pool    = torch.nn.functional.max_pool1d(desc_cnn, desc_cnn.size()[2]).squeeze_(2)
		desc_emb     = self.linear(desc_pool).clamp(min=0)

		return desc_emb


################################################################################################################################
# Product Encoder
#

class NameEncoder(DescriptionEncoder):

	def data(self, prod_list, repo, corpus):

		# Load context
		raw_name = [product.brand[0] + product.name_ws.txts for product in prod_list]

		# Encode
		name_code = self.meta.tokenizer.transform_sequences(raw_name)

		# Pad
		name_pad = self.meta.padder(name_code, padding='post')

		# Combine inputs
		name_pad_var = torch.from_numpy(name_pad).long()

		return name_pad_var,
