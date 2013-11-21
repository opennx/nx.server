#!/usr/bin/env python
# -*- coding: utf-8 -*-


from common import *
from time import *
import os





class MetaType(object):
	tag = ""
	

class MetaDict(object):
	def __init__(self):


class Asset(object):
	def __init__(self,id_asset=False,db=False):
		self.id_asset = id_asset
		if self.id_asset == -1:
			"""id_asset==-1 is reserved for live events"""
		elif self.id_asset:
			self._load(self.id_asset,db)
		else:
			self._new(self)

	def _load(self,id_asset,db=False):
		pass

	def _new(self):
		pass

	## Asset loading/creating
	#######################################
	## Special Getters

	def get_file_path(self):
		return False

	def get_duration(self):
		return False

	## Special Getters
	#######################################
	## Asset deletion

	def trash(self):
		pass

	def untrash(self):
		pass

	def purge(self):
		pass

	def make_offline(self):
		pass

	## Asset deletion
	#######################################
	## Getter / setter
