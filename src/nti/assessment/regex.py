#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from zope.container.contained import Contained

from dolmen.builtins.interfaces import IString

from persistent import Persistent

from nti.assessment.interfaces import IRegEx

from nti.contentfragments.interfaces import HTMLContentFragment

from nti.externalization.representation import WithRepr

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import createDirectFieldProperties

@WithRepr
@EqHash("pattern",)
@interface.implementer(IRegEx)
class RegEx(SchemaConfigured, Persistent, Contained):
	createDirectFieldProperties(IRegEx)

	__external_can_create__ = True
	mime_type = mimeType = 'application/vnd.nextthought.naqregex'

	def __init__(self, *args, **kwargs):
		Persistent.__init__(self)
		SchemaConfigured.__init__(self, *args, **kwargs)

	def __str__(self):
		return self.pattern
					
@component.adapter(IString)
@interface.implementer(IRegEx)
def _regex_str_adapter(pattern, solution=None):
	result = RegEx(pattern=pattern)
	result.solution = HTMLContentFragment(solution) if solution else None
	return result

@interface.implementer(IRegEx)
def _regex_collection_adapter(source):
	return _regex_str_adapter(source[0], source[1] if len(source) >= 2 else None)
