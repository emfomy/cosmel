#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import os
import sys

sys.path.insert(0, os.path.abspath('.'))
from styleme import *


if __name__ == '__main__':

	assert len(sys.argv) >= 2
	ver = sys.argv[1]

	replaced_pname = False
	added_role     = False

	target       = f'pruned_article'
	data_root    = f'data/{ver}'
	repo_root    = f'{data_root}/repo'
	ws_re_root   = f'{data_root}/article/{target}_ws_re2'
	ws_root      = f'{data_root}/article/{target}_ws'
	role_root    = f'{data_root}/article/{target}_role'
	parts        = ['']
	parts        = list(f'part-{x:05}' for x in range(1))
	if len(sys.argv) >= 3: parts = list(f'part-{x:05}' for x in range(int(sys.argv[2]), 128, 8))

	repo = Repo(repo_root)

	# Replace Product Name
	if not replaced_pname:

		pname_dict = dict()
		for product in repo.product_set:
			pname_dict[product.name] = product.name_ws

		articles = ArticleSet(ws_re_root, parts=parts)

		n = str(len(articles))
		for i, article in enumerate(articles):
			for sid, line in enumerate(article):
				for mid, txt in enumerate(line.txts):
					if txt in pname_dict:
						pname_ws = pname_dict[txt][:]
						if len(pname_ws) > 1:
							line.txts[mid] = str(pname_ws[:-1]) + '　' + pname_ws.txts[-1]
						else:
							line.txts[mid] = pname_ws.txts[-1]
						line.tags[mid] = pname_ws.tags[-1]

			# Write article to file
			ws_file = transform_path(article.path, ws_re_root, ws_root)
			os.makedirs(os.path.dirname(ws_file), exist_ok=True)
			printr(f'{i+1:0{len(n)}}/{n}\t{ws_file}')
			article.save(ws_file, str)

		print()

	# Add Role
	if not added_role:

		repo     = Repo(repo_root)
		articles = ArticleSet(ws_root, parts=parts)

		n = str(len(articles))
		for i, article in enumerate(articles):

			# Replace role article to file
			# for line in article:
			for sid, line in enumerate(article):
				for mid, txt in enumerate(line.txts):
					if   txt in repo.bname_to_brand: line.roles[mid] = 'Brand'
					elif txt in repo.head_set:       line.roles[mid] = 'Head'
					elif txt in repo.infix_set:      line.roles[mid] = 'Infix'

			# Write article to file
			role_file = transform_path(article.path, ws_root, role_root, '.role')
			os.makedirs(os.path.dirname(role_file), exist_ok=True)
			printr(f'{i+1:0{len(n)}}/{n}\t{role_file}')
			article.save(role_file, roledstr)

		print()

	pass
