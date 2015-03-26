#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time

from zope.datetime import parseDatetimetz

from nti.externalization.representation import WithRepr

from nti.schema.schema import EqHash

_marker = object()

from .interfaces import IQPart
from .interfaces import IQuestion
from .interfaces import IQuestionSet
from .interfaces import IQAssignment
from .interfaces import IQTimedAssignment

## classes

@WithRepr
@EqHash('value', superhash=True)
class TrivialValuedMixin(object):

	value = None

	def __init__(self, *args, **kwargs):
		# The contents of ``self.value`` come from either the first arg
		# (if positional args are given) or the kwarg name such.

		if args:
			value = args[0]
		elif 'value' in kwargs:
			value = kwargs.get('value')
		else:
			value = None

		# Avoid the appearance of trying to pass args to object.__init__ to avoid a Py3K warning
		init = super(TrivialValuedMixin, self).__init__
		if getattr(init, '__objclass__', None) is not object:  # object's init is a method-wrapper
			init(*args, **kwargs)

		if value is not None:
			self.value = value

	def __str__(self):
		return str(self.value)

## functions

def make_sublocations(child_attr='parts'):
	def sublocations(self):
		for part in getattr(self, child_attr, None) or ():
			if hasattr(part, '__parent__'):
				if part.__parent__ is None:
					part.__parent__ = self
				if part.__parent__ is self:
					yield part
	return sublocations

def dctimes_property_fallback(attrname, dcname):
	# For BWC, if we happen to have annotations that happens to include
	# zope dublincore data, we will use it
	# TODO: Add a migration to remove these
	def get(self):
		self._p_activate()  # make sure there's a __dict__
		if attrname in self.__dict__:
			return self.__dict__[attrname]
		if '__annotations__' in self.__dict__:
			try:
				dcdata = self.__annotations__['zope.app.dublincore.ZopeDublinCore']
				date_modified = dcdata[dcname]  # tuple of a string
				datetime = parseDatetimetz(date_modified[0])
				result = time.mktime(datetime.timetuple())
				self.__dict__[attrname] = result  # migrate
				self._p_changed = True
				return result
			except KeyError: # pragma: no cover
				pass
		return 0

	def _set(self, value):
		self.__dict__[attrname] = value

	return property(get, _set)

def iface_of_assessment(thing):
	iface = IQuestion
	if IQuestionSet.providedBy(thing):
		iface = IQuestionSet
	elif IQTimedAssignment.providedBy(thing):
		iface = IQTimedAssignment
	elif IQAssignment.providedBy(thing):
		iface = IQAssignment
	elif IQPart.providedBy(thing):
		iface = IQPart
	return iface
