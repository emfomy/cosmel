#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
.. codeauthor::
	 Mu Yang <emfomy@gmail.com>
"""

import collections.abc
import os
import re
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
		return str(self.__data)

	def __repr__(self):
		return str(self)


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
			(re.compile(r'[^0-9a-z\u4e00-\u9fff\n□]+'), ''), \
			(re.compile(r'□+($|[0-9\u4e00-\u9fff\n])'), r'\1'), \
			(re.compile(r'(\A|[0-9\u4e00-\u9fff\n])□+'), r'\1'), \
			(re.compile(r'spf([0-9]*)pa'), r'spf\1□pa'), \
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


def grep_files(root):
	"""Grep all files in the directory."""

	if os.path.isdir(root):
		return sorted([os.path.join(path, file) for path, _, files in os.walk(root) for file in files])
	else:
		return [root]


def printr(chars):
	"""Print with '\\\\r'"""
	print(str(chars).ljust(80)+'\r', end='')


def subprocess_call(command, *args, **kwargs):
	"""Print command before calling it."""
	print(command)
	subprocess.call(command, *args, **kwargs)
