#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
   Mu Yang <emfomy@gmail.com>
"""

from flask import Flask
from flask import abort
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request

import json
import os
import time

import sys
sys.path.append('..')
from styleme import *

app = Flask(__name__)

@app.route('/')
def index_route():
	global files
	aid = request.args.get('aid')
	return render_template('index.html', aid=aid, files=files)

@app.route('/prev')
def prev_route():
	global files
	try:
		idx = files.index(request.args.get('aid')) - 1
	except ValueError:
		idx = 0
	aid = files[idx] if idx >= 0 else None
	return redirect(f'/?aid={aid}', code=302)

@app.route('/next')
def next_route():
	global files
	try:
		idx = files.index(request.args.get('aid')) + 1
	except ValueError:
		idx = 0
	aid = files[idx] if idx < len(files) else None
	return redirect(f'/?aid={aid}', code=302)

@app.route('/repo')
def repo_route():
	global repo
	brand = request.args.get('brand')
	return '<br>'.join(map(str, repo.name_head_to_product_list[brand, :]))

@app.route('/article/<path:path>')
def article_route(path):
	with open(f'article/{path}.xml.html') as fin:
		data = fin.read()
	return str(data)

@app.route('/json/<path:path>')
def json_route(path):
	file = f'json/{path}.json'
	os.makedirs(os.path.dirname(file), exist_ok=True)
	with open(file) as fin:
		data = fin.read().replace('\n', '<br/>')
	return str(data)

@app.route('/save', methods=['POST'])
def save_route():
	try:
		data = request.data;
		aid = request.args.get('aid')
		json_data = json.loads(data)
		d = time.time()
		json_data['time'] = d
		json_data['date'] = time.strftime('%a %b %d %Y %H:%M:%S GMT%z (%Z)', time.localtime(d))
		print(aid, json_data)
		file = f'json/{aid}.json'
		os.makedirs(os.path.dirname(file), exist_ok=True)
		with open(file, 'a') as fout:
			fout.write(json.dumps(json_data)+'\n')
		return jsonify(message='')
	except Exception as e:
		print(f'"/save" failed: {e}')
		return jsonify(message=str(e)), 500

if __name__ == '__main__':
	global files
	global repo
	repo  = Repo('repo')
	part  = 'part-00000'
	ext   = '.xml.html'
	files = sorted([f'{part}/{file}'.replace(ext, '') for file in os.listdir(f'article/{part}') if file.endswith(ext)])
	app.run(host='140.109.19.229', debug=True)
