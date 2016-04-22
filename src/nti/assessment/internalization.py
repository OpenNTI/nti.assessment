#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import collections
from curses.ascii import isctrl

from zope import component
from zope import interface

from nti.assessment.interfaces import DISCLOSURE_TERMINATION

from nti.assessment.interfaces import IRegEx
from nti.assessment.interfaces import IQInquiry
from nti.assessment.interfaces import IWordEntry
from nti.assessment.interfaces import IQModeledContentResponse
from nti.assessment.interfaces import IQFillInTheBlankShortAnswerSolution
from nti.assessment.interfaces import IQFillInTheBlankWithWordBankSolution

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import IInternalObjectUpdater

from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

@component.adapter(IWordEntry)
@interface.implementer(IInternalObjectUpdater)
class _WordEntryUpdater(object):

	__slots__ = ('obj',)

	def __init__(self, obj):
		self.obj = obj

	def updateFromExternalObject(self, parsed, *args, **kwargs):
		if 'content' not in parsed or not parsed['content']:
			parsed['content'] = parsed['word']
		if parsed.get('lang'):
			parsed['lang'] = parsed['lang'].lower()
		result = InterfaceObjectIO(self.obj, IWordEntry).updateFromExternalObject(parsed)
		return result

@interface.implementer(IInternalObjectUpdater)
@component.adapter(IQFillInTheBlankShortAnswerSolution)
class _QFillInTheBlankShortAnswerSolutionUpdater(object):

	__slots__ = ('obj',)

	def __init__(self, obj):
		self.obj = obj

	def updateFromExternalObject(self, parsed, *args, **kwargs):
		value = parsed.get('value', {})
		for key in tuple(value.keys()): # mutating
			regex = value.get(key)
			if isinstance(regex, six.string_types):
				regex = IRegEx(regex)
			elif isinstance(regex, collections.Mapping):
				ext_obj = regex
				regex = find_factory_for(ext_obj)()
				update_from_external_object(regex, ext_obj)
			value[key] = regex

		result = InterfaceObjectIO(
					self.obj,
					IQFillInTheBlankShortAnswerSolution).updateFromExternalObject(parsed)
		return result

@interface.implementer(IInternalObjectUpdater)
@component.adapter(IQFillInTheBlankWithWordBankSolution)
class _QFillInTheBlankWithWordBankSolutionUpdater(object):

	__slots__ = ('obj',)

	def __init__(self, obj):
		self.obj = obj

	def updateFromExternalObject(self, parsed, *args, **kwargs):
		value = parsed.get('value', {})
		for key in tuple(value.keys()): # mutating
			data = value.get(key)
			if isinstance(data, six.string_types):
				data = data.split() # make it a list
				value[key] = data

		result = InterfaceObjectIO(
					self.obj,
					IQFillInTheBlankWithWordBankSolution).updateFromExternalObject(parsed)
		return result

@component.adapter(IQModeledContentResponse)
@interface.implementer(IInternalObjectUpdater)
class _QModeledContentResponseUpdater(object):

	__slots__ = ('obj',)

	def __init__(self, obj):
		self.obj = obj

	def updateFromExternalObject(self, parsed, *args, **kwargs):
		value = parsed.get('value', None)
		if value is not None:
			if isinstance(value, six.string_types):
				value = [value]
			for idx in xrange(len(value)):
				value[idx] = filter(lambda c: not isctrl(c), value[idx])
			parsed['value'] = value
		result = InterfaceObjectIO(
					self.obj,
					IQModeledContentResponse).updateFromExternalObject(parsed)
		return result

@component.adapter(IQInquiry)
@interface.implementer(IInternalObjectUpdater)
class _QInquiryUpdater(object):

	__slots__ = ('obj',)

	def __init__(self, obj):
		self.obj = obj

	def updateFromExternalObject(self, parsed, *args, **kwargs):
		value = parsed.get('disclosure', None) or DISCLOSURE_TERMINATION
		parsed['disclosure'] = value.lower()
		result = InterfaceObjectIO(
					self.obj,
					IQInquiry).updateFromExternalObject(parsed)
		return result
