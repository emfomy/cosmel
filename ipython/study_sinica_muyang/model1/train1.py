#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import argparse
import itertools
import os
import sys

import numpy as np

import torch
import torch.utils.data
from torch.nn.utils.rnn import pack_padded_sequence

sys.path.insert(0, os.path.abspath('.'))
from styleme import *
from meta import *


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

	def forward(self, title_pad, pre_pad, post_pad, pid_bag, brand_bag):

		local_emb = self.local_encoder(title_pad, pre_pad, post_pad)
		docu_emb  = self.docu_encoder(pid_bag, brand_bag)
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

	def forward(self, title_pad, pre_pad, post_pad):

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

	def forward(self, pid_bag, brand_bag):

		docu_emb = self.linear(torch.cat((pid_bag, brand_bag), dim=1)).clamp(min=0)

		return docu_emb


################################################################################################################################
# Name Encoder
#

class NameEncoder(torch.nn.Module):

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

	def forward(self, name_pad):

		name_pad_emb = self.word_emb(name_pad)
		name_cnn     = self.conv1d(name_pad_emb.permute(0, 2, 1))
		name_pool    = torch.nn.functional.max_pool1d(name_cnn, name_cnn.size()[2]).squeeze_(2)
		name_emb     = self.linear(name_pool).clamp(min=0)

		return name_emb


################################################################################################################################
# Model1e Encoder
#

class Model1e(torch.nn.Module):

	def __init__(self, meta):

		super().__init__()

		self.meta = meta

		# Get sizes
		num_vocab = len(meta.keyed_vectors.vocab)

		# Prepare embeddings
		vocab_embedding = meta.keyed_vectors[meta.keyed_vectors.index2word]
		vocab_embedding[0] = 0

		# Set dimensions
		self.w2v_emb_size = meta.keyed_vectors.vector_size

		# Create modules
		self.word_emb = torch.nn.Embedding(num_vocab, self.w2v_emb_size)
		self.word_emb.weight.data = torch.from_numpy(vocab_embedding)

		lstm_emb_size = 100
		self.text_encoder = ContextEncoder(meta, self.word_emb, lstm_emb_size)

		cnn_emb_size = 100
		cnn_win_size = 2
		self.cand_encoder = NameEncoder(meta, self.word_emb, cnn_emb_size, cnn_win_size)
		self.ment_encoder = NameEncoder(meta, self.word_emb, cnn_emb_size, cnn_win_size)

		cat_size = self.text_encoder.output_size + self.cand_encoder.output_size + self.ment_encoder.output_size
		self.classifier = torch.nn.Linear(cat_size, 1)

	def forward(self, title_pad, pre_pad, post_pad, pid_bag, brand_bag, cand_pad, ment_pad):

		text_emb = self.text_encoder(title_pad, pre_pad, post_pad, pid_bag, brand_bag)
		cand_emb = self.cand_encoder(cand_pad)
		ment_emb = self.ment_encoder(ment_pad)

		prob     = self.classifier(torch.cat((text_emb, cand_emb, ment_emb), dim=1)).sigmoid()

		return prob


if __name__ == '__main__':

	# Parse arguments
	argparser = argparse.ArgumentParser(description='Train StyleMe model.')

	arggroup = argparser.add_mutually_exclusive_group()
	arggroup.add_argument('-v', '--ver', metavar='<ver>#<date>', \
			help='set <dir> as "result/<ver>_<date>"')
	arggroup.add_argument('-D', '--dir', metavar='<dir>', \
			help='prepend <dir> to data and model path')

	argparser.add_argument('-d', '--data', metavar='<data_name>', required=True, \
			help='training data path; load data list from "[<dir>/]<data_name>.list.txt"')
	argparser.add_argument('-w', '--weight', metavar='<weight_name>', required=True, \
			help='output weight path; output model weight into "[<dir>/]<weight_name>.<model_type>.weight.pt"')
	argparser.add_argument('--meta', metavar='<meta_name>', \
			help='dataset meta path; default is "[<dir>/]meta.pkl"')

	argparser.add_argument('-c', '--check', action='store_true', help='Check arguments')

	args = argparser.parse_args()

	vers          = args.ver.split('#')
	ver           = vers[0]
	date          = ''
	if len(vers) > 1:
		date        = f'_{vers[1]}'

	result_root = ''
	if args.ver != None:
		result_root = f'result/{ver}{date}/'
	if args.dir != None:
		result_root = f'{args.dir}/'

	model_name    = f'model1e'
	data_file     = f'{result_root}{args.data}.list.txt'
	model_file    = f'{result_root}{args.weight}.{model_name}.pt'

	meta_file     = f'{result_root}meta.pkl'
	if args.meta != None:
		meta_file = args.meta

	# Print arguments
	print()
	print(args)
	print()
	print(f'model         = {model_name}')
	print(f'data_file     = {data_file}')
	print(f'model_file    = {model_file}')
	print(f'meta_file     = {meta_file}')

	if args.check: exit()

	############################################################################################################################
	# Create model
	#

	meta  = DataSetMeta.load(meta_file)
	model = Model1e(meta)
	model.cuda()
	print()
	print(model)
	print()

	############################################################################################################################
	# Load data
	#

	asmid_list = AsmidList.load(data_file)

	parts  = list(set(m.aid for m in asmid_list))
	repo   = Repo(meta.repo_path)
	corpus = Corpus(meta.article_path, meta.mention_path, parts=parts)

	orig_ment_list = [corpus.id_to_mention[asmid.asmid] for asmid in asmid_list]
	orig_ment_list = orig_ment_list[:10]
	for m, asmid in zip(orig_ment_list, asmid_list):
		m.set_gid(asmid.gid)
		m.set_pid(asmid.pid)
	for m in orig_ment_list:
		if m.gid == 'NAP': m.set_gid('GP')
		if m.pid == 'NAP': m.set_pid('GP')

	cand_ment_list = [(m, c) for m in orig_ment_list for c in repo.brand_head_to_product_list[:, m.head]]
	cand_num       = [len(repo.brand_head_to_product_list[:, m.head]) for m in orig_ment_list]

	ment_list = [m for (m, _) in cand_ment_list]
	cand_list = [c for (_, c) in cand_ment_list]

	print(f'nun_train (orig) = {len(orig_ment_list)}')
	print(f'nun_train        = {len(ment_list)}')

	############################################################################################################################
	# Local context data
	#

	# Load context
	max_num_sentences = 5

	raw_title = [ \
			mention.article[0].txts for mention in ment_list \
	]
	raw_pre  = [ \
			list(itertools.chain( \
					itertools.chain.from_iterable( \
							s.txts for s in mention.article[relu(mention.sid-max_num_sentences):mention.sid] \
					), \
					mention.sentence_pre_().txts \
			)) for mention in ment_list \
	]
	raw_post = [ \
			list(itertools.chain( \
					mention.sentence_post_().txts, \
					itertools.chain.from_iterable( \
							s.txts for s in mention.article[mention.sid+1:mention.sid+1+max_num_sentences] \
					) \
			)) for mention in ment_list \
	]

	# Encode
	title_code = meta.tokenizer.transform_sequences(raw_title)
	pre_code   = meta.tokenizer.transform_sequences(raw_pre)
	post_code  = meta.tokenizer.transform_sequences(raw_post)

	# Pad
	title_pad = meta.padder(title_code, padding='post')
	pre_pad   = meta.padder(pre_code,   padding='pre')
	post_pad  = meta.padder(post_code,  padding='post')

	# Convert to variable
	title_pad_var = torch.autograd.Variable(torch.from_numpy(title_pad).long(), requires_grad=False).cuda()
	pre_pad_var   = torch.autograd.Variable(torch.from_numpy(pre_pad).long(),   requires_grad=False).cuda()
	post_pad_var  = torch.autograd.Variable(torch.from_numpy(post_pad).long(),  requires_grad=False).cuda()

	############################################################################################################################
	# Document context data
	#

	# Load bag
	raw_pid_bag   = [set(m.pid for m in mention.bundle if m.rule == 'P_rule1') for mention in ment_list]
	raw_brand_bag = [ \
			set(repo.bname_to_brand[t[0]][0] \
					for t in itertools.chain.from_iterable(sentence.zip3 for sentence in mention.article) if t[2] == 'Brand' \
			) for mention in ment_list \
	]

	# Encode
	pid_bag   = meta.p_multibinarizer.transform(raw_pid_bag)
	brand_bag = meta.b_multibinarizer.transform(raw_brand_bag)

	# Convert to variable
	pid_bag_var   = torch.autograd.Variable(torch.from_numpy(pid_bag).float(),   requires_grad=False).cuda()
	brand_bag_var = torch.autograd.Variable(torch.from_numpy(brand_bag).float(), requires_grad=False).cuda()

	############################################################################################################################
	# Candidate and mention data
	#

	# Load name
	raw_cand = [list(product.brand) + product.name_ws.txts for product in cand_list]
	raw_ment = [mention.sentence_pre_().txts[-10:] for mention in ment_list]

	# Encode
	cand_code = meta.tokenizer.transform_sequences(raw_cand)
	ment_code = meta.tokenizer.transform_sequences(raw_ment)

	# Pad
	cand_pad  = meta.padder(cand_code, padding='post')
	ment_pad  = meta.padder(ment_code, padding='post')

	# Convert to variable
	cand_pad_var = torch.autograd.Variable(torch.from_numpy(cand_pad).long(), requires_grad=False).cuda()
	ment_pad_var = torch.autograd.Variable(torch.from_numpy(ment_pad).long(), requires_grad=False).cuda()

	############################################################################################################################
	# Label data
	#

	# Load label
	label = np.array([(m.gid == c.pid) for (m, c) in cand_ment_list], dtype='float32')

	# Convert to variable
	y = torch.autograd.Variable(torch.from_numpy(label).float(), requires_grad=False).cuda()

	############################################################################################################################
	# Training
	#

	# Create optimizer
	optimizer = torch.optim.Adam(model.parameters())
	criterion = torch.nn.BCELoss()

	# Train
	num_epoch = 20
	for epoch in range(num_epoch):

		y_pred = model(title_pad_var, pre_pad_var, post_pad_var, pid_bag_var, brand_bag_var, cand_pad_var, ment_pad_var)
		loss = criterion(y_pred, y)
		print(f'Epoch: {epoch+1:0{len(str(num_epoch))}}/{num_epoch} | loss: {loss.item()}')

		optimizer.zero_grad()
		loss.backward()
		optimizer.step()

	# Save models
	model.save(model_file)
	print(f'Saved training model into "{model_file}"')

	pass
