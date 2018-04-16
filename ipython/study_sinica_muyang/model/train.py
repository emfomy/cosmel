#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'

import argparse
import os
import sys

import numpy as np

import torch
from torch.nn.utils.rnn import pack_padded_sequence

sys.path.insert(0, os.path.abspath('.'))
from styleme import *
from data import DataPack
from model2 import Model2 as Model


if __name__ == '__main__':

	# Parse arguments
	argparser = argparse.ArgumentParser(description='Train StyleMe model.')

	arggroup = argparser.add_mutually_exclusive_group()
	arggroup.add_argument('-v', '--ver', metavar='<ver>#<date>', \
			help='set <dir> as "result/<ver>_<date>"')
	arggroup.add_argument('-D', '--dir', metavar='<dir>', \
			help='append extensions to data and model path; use ".data.pkl" for data, ".model.pt" for model.')

	argparser.add_argument('-d', '--data', metavar='<data_name>', required=True, \
			help='training data path; load data from "[<dir>/]<data_name>.data.pkl"')
	argparser.add_argument('-m', '--model', metavar='<model_name>', required=True, \
			help='output model path; output training model into "[<dir>/]<model_name>.model.pt", '+ \
				'and predicting model into "[<dir>/]<model_name>.predict.model"')
	argparser.add_argument('-p', '--pretrain', metavar='<pretrained_name>', \
			help='pretrained model path; load model from "[<dir>/]<pretrained_name>.model.pt"')

	argparser.add_argument('-c', '--check', action='store_true', help='Check arguments.')

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

	data_file     = f'{result_root}{args.data}.data.pkl'
	model_file    = f'{result_root}{args.model}.model.pt'

	pretrain_file = ''
	if args.pretrain != None:
		pretrain_file = f'{result_root}{args.pretrain}.model.pt'

	# Print arguments
	print()
	print(args)
	print()
	print(f'data_file     = {data_file}')
	print(f'model_file    = {model_file}')
	print(f'pretrain_file = {pretrain_file}')
	print()

	if args.check: exit()

	# Load data
	pack = DataPack.load(data_file)
	num_train = pack.data.gid_code.shape[0]
	print(f'num_train       = {num_train}')

	# Create model
	model = Model(pack.info)
	print()
	print(model)
	print()

	# Create inputs
	inputs = model.inputs(pack)

	# Use GPU
	model.cuda()
	inputs.cuda()

	# Train the model
	optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()))
	for epoch in range(100):

		# Forward and compute loss
		text_loss, desc_loss = model(**vars(inputs))

		text_loss_data = text_loss.data[0]
		desc_loss_data = desc_loss.data[0]
		loss_data      = text_loss.data[0] + desc_loss.data[0]
		print(f'Epoch: {epoch:2d} | loss: {loss_data:.6f} | text_loss: {text_loss_data:.6f} | desc_loss: {desc_loss_data:.6f}')

		optimizer.zero_grad()
		text_loss.backward()
		desc_loss.backward()
		optimizer.step()

	# Save models
	model.save(model_file)
	print(f'Saved training model into "{model_file}"')

	from predict import model_accuracy
	predict_prob = model.predict(**vars(inputs)).cpu().data.numpy()
	predict_gid_code = np.argmax(predict_prob, axis=1)
	model_accuracy(predict_gid_code, pack.data.gid_code)
	model_accuracy(predict_gid_code, pack.data.gid_code, pack.data.rule == 'P_rule1', 'P_rule1')

	pass
