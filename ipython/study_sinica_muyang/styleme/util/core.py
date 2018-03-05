#!/usr/bin/env python3
# -*- coding:utf-8 -*-


__author__    = 'Mu Yang <emfomy@gmail.com>'
__copyright__ = 'Copyright 2017-2018'


import collections.abc
import glob
import os
import re
import shutil
import subprocess

from styleme.util.core import *


class ReadOnlyList(collections.abc.Sequence):
	"""The read-only list class."""

	def __init__(self, data = []):
		super().__init__()
		self.__data = list(data)

	def __contains__(self, item):
		return item in self.__data

	def __getitem__(self, key):
		return self.__data[key]

	def __iter__(self):
		return iter(self.__data)

	def __len__(self):
		return len(self.__data)

	def __str__(self):
		return str(list(str(item) for item in self.__data))

	def __repr__(self):
		return str(self.__data)


def prune_string(chars):
	"""
	* Convert to lower cases.
	* Remove special symbols.
	* Remove spaces near non-alphabets.
	"""
	return PruneString.sub(chars)

class PruneString():

	__regexes = [ \
			(re.compile(r'[^\S\n]'), r'□'), \
			(re.compile(r'[^0-9a-z\u4e00-\u9fff、\n□]+'), ''), \
			(re.compile(r'□+($|[0-9\u4e00-\u9fff、\n])'), r'\1'), \
			(re.compile(r'(\A|[0-9\u4e00-\u9fff、\n])□+'), r'\1'), \
			(re.compile(r'([0-9]*)pa($|[^a-z])'), r'\1□pa\2'), \
			(re.compile(r'\n+'), '\n'), \
			(re.compile(r'□+'), '□')]

	def __init__(self):
		raise Exception

	@classmethod
	def sub(self, chars):
		chars = chars.lower()
		for regex in self.__regexes:
			chars = regex[0].sub(regex[1], chars)
		return chars


def check_contain_chinese(chars):
	"""Check if containing Chinese characters."""
	for c in chars:
		if '\u4e00' <= c <= '\u9fff':
			return True
	return False


def grep_files(root, parts=['']):
	"""Grep all files in the directory."""

	retval = set()
	for part in parts:
		subroot = root+'/'+part
		if os.path.isdir(subroot):
			retval.update([os.path.join(path, file) for path, _, files in os.walk(subroot) for file in files])
		elif os.path.isfile(subroot):
			retval.add(subroot)
		else:
			retval.update(glob.glob(f'{subroot}.*'))
	return sorted(retval)


def rm_files(root, parts=['']):
	"""Remove files in the directory."""
	for part in parts:
		subroot = root+'/'+part
		if os.path.exists(subroot):
			shutil.rmtree(subroot)

def transform_path(path, old_root, new_root, new_ext=None):
	"""Transform path."""
	head, tail = os.path.split(path)
	head = head.replace(old_root, new_root)
	if new_ext: tail = os.path.splitext(tail)[0]+new_ext
	return f'{head}/{tail}'


def printr(*objects):
	"""Print with '\\\\r'."""
	print('\033[K'+' '.join(map(str, objects)), end='\r')


def colored(code, string):
	"""Color string."""
	return f'\033[{code}m{string}\033[0m'


def relu(x):
	"""ReLU function."""
	return max(x, 0)


def pause():
	"""Pause until pressing Enter."""
	input("Press Enter to continue...")


def subprocess_call(command, *args, **kwargs):
	"""Print command before calling it."""
	print(command)
	subprocess.call(command, *args, **kwargs)
