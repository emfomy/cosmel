#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


from flask import abort
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

import json
import os
import sys
import time

from cosmel import *

app = Flask(__name__)

def root():
	global ver
	return ver

@app.route('/')
def index_route():
	global files

	part = request.args.get('part')
	aid  = request.args.get('aid')
	act  = request.args.get('act')
	do_redirect = False

	if 'part' not in request.args or part not in files:
		part = list(files.keys())[0]
		aid  = None
		act  = None
		do_redirect = True

	if aid == 'None':
		aid = None
	if 'aid' in request.args and aid not in files[part]:
		aid = None
		act = None
		do_redirect = True

	if 'act' in request.args:
		idx = files[part].index(aid)
		if act == 'prev': idx -= 1
		if act == 'next': idx += 1
		aid = files[part][idx % len(files[part])]
		act = None
		do_redirect = True

	if do_redirect:
		args = dict()
		if part: args['part'] = part
		if aid:  args['aid']  = aid
		if act:  args['act']  = act
		return redirect(url_for('index_route', **args), code=302)

	mention_data = dict()
	try:
		file = f'{root()}/mention/{part}/{aid}.json'
		with open(file) as fin:
			for json_line in [json.loads(line) for line in fin]:
				mention_data[f'{json_line["sid"]}-{json_line["mid"]}'] = json_line
	except Exception as e:
		print(colored('1;31', e))

	json_data = dict()
	try:
		file = f'{root()}/json/{part}/{aid}.json'
		with open(file) as fin:
			for json_line in [json.loads(line) for line in fin]:
				json_data[f'{json_line["sid"]}-{json_line["mid"]}'] = json_line
	except Exception as e:
		print(colored('1;31', e))

	print(mention_data)
	print(json_data)

	return render_template('index.html', ver=root(), aid=aid, part=part, files=files, \
			mention_data=mention_data, json_data=json_data)

@app.route('/repo/product')
def product_route():
	global repo
	pid   = request.args.get('pid')
	brand = request.args.get('brand', default=slice(None))
	head  = request.args.get('head',  default=slice(None))
	print(pid, brand, head)
	def id_to_product_get(pid):
		if pid == '':      return ''
		elif pid == 'OSP': return 'OSP [Other-Specific-Product]'
		elif pid == 'GP':  return 'GP [Genreal-Product]'
		elif pid == 'NAP': return 'NAP [Not-A-Product]'
		else:              return str(repo.id_to_product.get(pid, f'{pid} [KeyError]'))
	if pid: return '<hr>'.join('<br>'.join(id_to_product_get(p) for p in pp.split(',')) for pp in pid.split(';'))
	else:   return '<br>'.join(map(str, repo.bname_head_to_product_list[brand, head]))
	# else: return '\t'.join(repo.bname_to_brand[brand])+'<br>' + \
	# 		'<br>'.join(map(str, repo.bname_head_to_product_list[brand, head]))

@app.route('/article/<path:path>')
def article_route(path):
	try:
		file = f'{root()}/article/{path}.xml.html'
		with open(file) as fin:
			data = fin.read()
		return str(data)
	except Exception as e:
		print(colored('1;31', e))
		return ''

@app.route('/json/<path:path>')
def json_route(path):
	data = ''

	file = f'{root()}/mention/{path}.json'
	try:
		with open(file) as fin:
			data += fin.read().replace('\n', '<br>')
	except Exception as e:
		print(colored('1;31', e))

	data += '<hr>'

	file = f'{root()}/json/{path}.json'
	try:
		with open(file) as fin:
			data += fin.read().replace('\n', '<br>')
	except Exception as e:
		print(colored('1;31', e))

	return data

@app.route('/save', methods=['POST'])
def save_route():
	try:
		data = request.data
		part = request.args.get('part')
		aid = request.args.get('aid')
		json_data = json.loads(data)
		d = time.time()
		json_data['time'] = d
		json_data['date'] = time.strftime('%a %b %d %Y %H:%M:%S GMT%z (%Z)', time.localtime(d))
		print(aid, json_data)
		file = f'{root()}/json/{part}/{aid}.json'
		os.makedirs(os.path.dirname(file), exist_ok=True)
		with open(file, 'a') as fout:
			fout.write(json.dumps(json_data)+'\n')
		return jsonify(message='')
	except Exception as e:
		print(colored('1;31', e))
		return jsonify(message=str(e)), 500

if __name__ == '__main__':

	global ver
	assert len(sys.argv) > 1
	ver  = sys.argv[1]
	host = '0.0.0.0'

	global repo
	repo  = Repo(f'{root()}/repo')
	ext   = '.xml.html'

	global files
	parts = sorted([part for part in os.listdir(f'{root()}/article') if os.path.isdir(f'{root()}/article/{part}')])
	files = dict()
	for part in parts:
		files[part] = [None] + \
				sorted([file.replace(ext, '') for file in os.listdir(f'{root()}/article/{part}') if file.endswith(ext)], \
					key=lambda v: v.upper())

	app.run(host=host, port=5000, threaded=True, debug=False)
