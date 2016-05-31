#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

def _patch():
	import os
	import sys
	import inspect
	import importlib

	from nti.assessment.interfaces import IQPart
	from nti.assessment.interfaces import IQAssessment
	module = sys.modules[IQAssessment.__module__]

	# main package name
	package = '.'.join(module.__name__.split('.')[:-1])

	# set mimetypes on interfaces
	for name in os.listdir(os.path.dirname(__file__)):
		# ignore modules we may have trouble importing
		if 		name in ('jsonschema.py',
						 'externalization.py',
						 'internalization.py',
						 'wref.py') \
			or	name[-3:] != '.py' \
			or  name.startswith( '_' ):
			continue

		try:
			module = package + '.' + name[:-3]
			module = importlib.import_module(module)
		except ImportError:
			continue
		for _, item in inspect.getmembers(module):
			try:
				mimeType = getattr(item, 'mimeType', getattr(item, 'mime_type'))
				# first interface is the externalizable object
				interfaces = tuple(item.__implemented__.interfaces())
				root = interfaces[0]
				root.setTaggedValue('_ext_mime_type', mimeType)
				if root.isOrExtends( IQPart ):
					root.setTaggedValue('_ext_jsonschema', u'part')

			except (AttributeError, TypeError):
				pass

_patch()
del _patch

def patch():
	pass
