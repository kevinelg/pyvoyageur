#!/usr/bin/env python
# encoding: utf-8
"""
MyUtils.py

Useful utilities

Created by Jonathan Neuhaus on 2010-04-14.
Copyright (c) 2010 HE-Arc. All rights reserved.
"""

# import sys
# import os

def speedMeasure(func):
	"""Time elapsed during the function"""
	import time
	def wrapper(*arg):
		t1 = time.clock()
		res = func(*arg)
		t2 = time.clock()
		print "%s took %0.3f ms" % (func.func_name, (t2-t1)*1000.0)
		return res
	return wrapper

