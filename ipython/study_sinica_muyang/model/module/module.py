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
		self.docu_encoder  = DocumentEncoder(meta, word_emb_module)

		self.linear = torch.nn.Linear(self.local_encoder.output_size + self.docu_encoder.output_size, self.output_size)

	def inputs(self, raw):

		# Combine inputs
		from .dataset import Inputs
		inputs = Inputs()
		inputs.local = self.local_encoder.inputs(raw)
		inputs.docu  = self.docu_encoder.inputs(raw)
		return inputs

	def forward(self, inputs):

		local_emb = self.local_encoder(inputs.local)
		docu_emb  = self.docu_encoder(inputs.docu)
		text_emb  = self.linear(torch.cat((local_emb, docu_emb), dim=1)).clamp(min=0)

		return text_emb


class LocalContextEncoder(torch.nn.Module):

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
		self.pre_lstm   = torch.nn.LSTM(w2v_emb_size, lstm_emb_size, batch_first=True)
		self.post_lstm  = torch.nn.LSTM(w2v_emb_size, lstm_emb_size, batch_first=True)

		lstm_cat_size  = lstm_size(self.title_lstm) + lstm_size(self.pre_lstm) + lstm_size(self.post_lstm)
		self.linear = torch.nn.Linear(lstm_cat_size, self.output_size)

	def inputs(self, raw):

		max_num_sentences = 5

		# Load context
		raw_title = [ \
				mention.article[0].txts for mention in raw.sublist \
		]
		raw_pre  = [ \
				list(itertools.chain( \
						itertools.chain.from_iterable( \
								s.txts for s in mention.article[relu(mention.sid-max_num_sentences):mention.sid] \
						), \
						mention.sentence_pre_().txts \
				)) for mention in raw.sublist \
		]
		raw_post = [ \
				list(itertools.chain( \
						mention.sentence_post_().txts, \
						itertools.chain.from_iterable( \
								s.txts for s in mention.article[mention.sid+1:mention.sid+1+max_num_sentences] \
						) \
				)) for mention in raw.sublist \
		]

		# Encode
		title_code = self.meta.tokenizer.transform_sequences(raw_title)
		pre_code   = self.meta.tokenizer.transform_sequences(raw_pre)
		post_code  = self.meta.tokenizer.transform_sequences(raw_post)

		# Pad
		title_pad  = self.meta.padder(title_code, padding='post')
		pre_pad    = self.meta.padder(pre_code,   padding='pre')
		post_pad   = self.meta.padder(post_code,  padding='post')

		# Combine inputs
		from .dataset import Inputs
		inputs = Inputs()
		inputs.title_pad = torch.autograd.Variable(torch.from_numpy(title_pad).long())
		inputs.pre_pad   = torch.autograd.Variable(torch.from_numpy(pre_pad).long())
		inputs.post_pad  = torch.autograd.Variable(torch.from_numpy(post_pad).long())
		return inputs

	def forward(self, inputs):

		title_pad = inputs.title_pad
		pre_pad   = inputs.pre_pad
		post_pad  = inputs.post_pad

		title_pad_emb = self.word_emb(title_pad)
		pre_pad_emb   = self.word_emb(pre_pad)
		post_pad_emb  = self.word_emb(post_pad)

		title_lstm0, _ = self.title_lstm(title_pad_emb)
		pre_lstm0, _   = self.pre_lstm(pre_pad_emb)
		post_lstm0, _  = self.post_lstm(post_pad_emb)

		title_lstm = title_lstm0[:, -1, :]
		pre_lstm   = pre_lstm0[:, -1, :]
		post_lstm  = post_lstm0[:, -1, :]

		local_emb = self.linear(torch.cat((title_lstm, pre_lstm, post_lstm), dim=1)).clamp(min=0)

		return local_emb


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

	def inputs(self, raw):

		# Load bag
		raw_pid_bag   = [set(m.pid for m in mention.bundle if m.rule == 'P_rule1') for mention in raw.sublist]
		raw_brand_bag = [ \
				set(raw.repo.bname_to_brand[t[0]][0] \
						for t in itertools.chain.from_iterable(sentence.zip3 for sentence in mention.article) if t[2] == 'Brand' \
				) for mention in raw.sublist \
		]

		# Encode
		pid_bag   = self.meta.p_multibinarizer.transform(raw_pid_bag)
		brand_bag = self.meta.b_multibinarizer.transform(raw_brand_bag)

		# Combine inputs
		from .dataset import Inputs
		inputs = Inputs()
		inputs.pid_bag   = torch.autograd.Variable(torch.from_numpy(pid_bag).float())
		inputs.brand_bag = torch.autograd.Variable(torch.from_numpy(brand_bag).float())
		return inputs

	def forward(self, inputs):

		pid_bag   = inputs.pid_bag
		brand_bag = inputs.brand_bag

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

	def inputs(self, raw):

		# Load context
		raw_desc = [product.descr_ws.txts for product in raw.sublist]

		# Encode
		desc_code = self.meta.tokenizer.transform_sequences(raw_desc)

		# Pad
		desc_pad = self.meta.padder(desc_code, padding='post')

		# Combine inputs
		from .dataset import Inputs
		inputs = Inputs()
		inputs.desc_pad = torch.autograd.Variable(torch.from_numpy(desc_pad).long())
		return inputs

	def forward(self, inputs):

		desc_pad = inputs.desc_pad

		desc_pad_emb = self.word_emb(desc_pad)
		desc_cnn     = self.conv1d(desc_pad_emb.permute(0, 2, 1))
		desc_pool    = torch.nn.functional.max_pool1d(desc_cnn, desc_cnn.size()[2]).squeeze_(2)
		desc_emb     = self.linear(desc_pool).clamp(min=0)

		return desc_emb


################################################################################################################################
# Product Encoder
#

class NameEncoder(DescriptionEncoder):

	def inputs(self, raw):

		# Load context
		raw_name = [list(product.brand) + product.name_ws.txts for product in sublist]

		# Encode
		name_code = self.meta.tokenizer.transform_sequences(raw_name)

		# Pad
		name_pad = self.meta.padder(name_code, padding='post')

		# Combine inputs
		from .dataset import Inputs
		inputs = Inputs()
		inputs.desc_pad = torch.autograd.Variable(torch.from_numpy(name_pad).long())
		return inputs
