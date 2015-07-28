#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Decorators for assessment objects.

.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import collections

from zope import interface
from zope import component

from nti.externalization.singleton import SingletonDecorator
from nti.externalization.externalization import to_external_object
from nti.externalization.interfaces import IExternalObjectDecorator
from nti.externalization.interfaces import IExternalMappingDecorator

from .interfaces import IQPart
from .interfaces import IRegEx
from .interfaces import IQMathPart
from .interfaces import IQPartSolutionsExternalizer
from .interfaces import IQFillInTheBlankShortAnswerPart
from .interfaces import IQFillInTheBlankWithWordBankPart
from .interfaces import IQFillInTheBlankShortAnswerSolution
from .interfaces import IQFillInTheBlankWithWordBankSolution

@interface.implementer(IQPartSolutionsExternalizer)
@component.adapter(IQPart)
class _DefaultPartSolutionsExternalizer(object):

	def __init__(self, part):
		self.part = part

	def to_external_object(self):
		return to_external_object(self.part.solutions)

@interface.implementer(IQPartSolutionsExternalizer)
@component.adapter(IQFillInTheBlankShortAnswerPart)
class _FillInTheBlankShortAnswerPartSolutionsExternalizer(object):

	def __init__(self, part):
		self.part = part

	def to_external_object(self):
		result = []
		for solution in self.part.solutions:
			ext = to_external_object(solution)
			if IQFillInTheBlankShortAnswerSolution.providedBy(solution):
				value = {}
				for k, v in solution.value.items():
					txt = v.solution if IRegEx.providedBy(v) else v
					value[k] = txt
				ext['value'] = value
		return result

@interface.implementer(IQPartSolutionsExternalizer)
@component.adapter(IQFillInTheBlankWithWordBankPart)
class _FillInTheBlankWithWordBankPartSolutionsExternalizer(object):

	def __init__(self, part):
		self.part = part

	def to_external_object(self):
		result = []
		for solution in self.part.solutions:
			ext = to_external_object(solution)
			if IQFillInTheBlankWithWordBankSolution.providedBy(solution):
				value = ext.get('value', {})
				for k in list(value.keys()):
					v = value.get(k)
					if 	v and not isinstance(v, six.string_types) and \
						isinstance(v, collections.Sequence):
						value[k] = v[0]  # pick first one always
			result.append(ext)
		return result

@interface.implementer(IExternalMappingDecorator)
@component.adapter(IQMathPart)
class _MathPartDecorator(object):
	"""
	Display the allowed_units sans solutions in the math part.
	"""

	def __init__(self, part):
		self.part = part

	def decorateExternalMapping(self, original, external):
		# For this use-case, the client just wants to display *some*
		# units.  So we just give them the flattened units.
		all_allowed_units = []
		for solution in self.part.solutions:
			allowed_units = getattr(solution, 'allowed_units', None)
			if allowed_units:
				all_allowed_units.extend([x for x in allowed_units])
		external['allowed_units'] = all_allowed_units
		return external

@interface.implementer(IExternalObjectDecorator)
class _QAssessmentObjectIContainedAdder(object):
	"""
	When an assignment or question set comes from a content package
	and thus has a __parent__ that has an NTIID, make that NTIID
	available as the ``containerId``, just like an
	:class:`nti.dataserver.interfaces.IContained` object. This is
	meant to help provide contextual information for the UI because
	sometimes these objects (assignments especially) are requested
	in bulk without any other context.

	Obviously this only works if assignments are written in the TeX
	files at a relevant location (within the section aka lesson they
	are about)---if they are lumped together at the end, this does no
	good.

	This is perhaps a temporary measure as assessments will be moving
	into course definitions.
	"""

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, context, mapping):
		if not mapping.get('containerId'):
			# Be careful not to write this out at rendering time
			# with a None value, but if it does happen overwrite it
			containerId = None
			containerId = getattr(context.__parent__, 'ntiid', None)
			if containerId:
				mapping['containerId'] = containerId

@interface.implementer(IExternalObjectDecorator)
class _QAssignmentObjectDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, context, mapping):
		mapping['NoSubmit'] = bool(context.no_submit)
		mapping['CategoryName'] = context.category_name

@interface.implementer(IExternalObjectDecorator)
class _QInquiryObjectDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, context, mapping):
		mapping.pop('no_submit', None)
		mapping['isClosed'] = bool(context.closed)
