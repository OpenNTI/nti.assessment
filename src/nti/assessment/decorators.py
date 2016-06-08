#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Decorators for assessment objects.

.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.assessment.common import get_containerId

from nti.assessment.interfaces import IQPart
from nti.assessment.interfaces import IQMathPart 
from nti.assessment.interfaces import IVersioned 

from nti.externalization.interfaces import IExternalObjectDecorator
from nti.externalization.interfaces import IExternalMappingDecorator

from nti.externalization.singleton import SingletonDecorator

@component.adapter(IQPart)
@interface.implementer(IExternalMappingDecorator)
class _RandomizedPartDecorator(object):

	def __init__(self, part):
		self.part = part

	def decorateExternalMapping(self, original, external):
		if not original.randomized:
			external.pop('randomized', None)
		return external

@component.adapter(IQMathPart)
@interface.implementer(IExternalMappingDecorator)
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

@component.adapter(IVersioned)
@interface.implementer(IExternalObjectDecorator)
class _VersionedDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, context, mapping):
		if not mapping.get('version'):
			mapping.pop('version', None)

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
			containerId = get_containerId(context)
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
