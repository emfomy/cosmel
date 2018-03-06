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

import glob
import json
import os
import time
import operator

from styleme import *

app = Flask(__name__)

@app.route('/')
def index_route():
	global files

	part = request.args.get('part')
	aid  = request.args.get('aid')
	act  = request.args.get('act')
	do_redirect = False

	if 'part' not in request.args or part not in files:
		part = list(files.keys())[0]
		do_redirect = True

	if 'aid' in request.args and aid not in files[part]:
		aid  = None
		do_redirect = True

	if 'act' in request.args:
		try:
			idx = files[part].index(aid)
			if act == 'prev': idx -= 1
			if act == 'next': idx += 1
		except ValueError:
			idx = 0
		finally:
			aid = files[part][idx] if 0 <= idx < len(files[part]) else None
			act = None
			do_redirect = True

	if do_redirect:
		args = dict()
		if part: args['part'] = part
		if aid:  args['aid']  = aid
		if act:  args['act']  = act
		return redirect(url_for('index_route', **args), code=302)

	json_data = dict()
	try:
		file = f'json/{part}/{aid}.json'
		with open(file) as fin:
			for line in sorted([json.loads(line) for line in fin], key=operator.itemgetter('time')):
				json_data[f'{line["sid"]}-{line["mid"]}'] = line['gid']
	except Exception as e:
		print(e)
		pass
	return render_template('index.html', aid=aid, part=part, files=files, json_data=json_data)

@app.route('/repo/product')
def product_route():
	global repo
	pid   = request.args.get('pid')
	brand = request.args.get('brand', default=slice(None))
	head  = request.args.get('head',  default=slice(None))
	if pid:   return '<br>'.join(str(repo.id_to_product.get(p, f'{p} [KeyError]')) for p in pid.split(','))
	else:     return '<br>'.join(map(str, repo.b_name_head_to_product_list[brand, head]))

@app.route('/article/<path:path>')
def article_route(path):
	file = f'article/{path}.xml.html'
	with open(file) as fin:
		data = fin.read()
	return str(data)

@app.route('/json/<path:path>')
def json_route(path):
	file = f'json/{path}.json'
	with open(file) as fin:
		data = fin.read().replace('\n', '<br/>')
	return str(data)

@app.route('/save', methods=['POST'])
def save_route():
	try:
		data = request.data;
		part = request.args.get('part')
		aid = request.args.get('aid')
		json_data = json.loads(data)
		d = time.time()
		json_data['time'] = d
		json_data['date'] = time.strftime('%a %b %d %Y %H:%M:%S GMT%z (%Z)', time.localtime(d))
		print(aid, json_data)
		file = f'json/{part}/{aid}.json'
		os.makedirs(os.path.dirname(file), exist_ok=True)
		with open(file, 'a') as fout:
			fout.write(json.dumps(json_data)+'\n')
		return jsonify(message='')
	except Exception as e:
		print(f'"/save" failed: {e}')
		return jsonify(message=str(e)), 500

if __name__ == '__main__':
	global repo
	repo  = Repo(f'repo')
	ext   = '.xml.html'

	global files
	parts = sorted([part for part in os.listdir(f'article') if os.path.isdir(f'article/{part}')])
	files = dict()
	for part in parts:
		files[part] = sorted([file.replace(ext, '') for file in os.listdir(f'article/{part}') if file.endswith(ext)])

	app.run(host='140.109.19.229', port=5000, debug=True)
