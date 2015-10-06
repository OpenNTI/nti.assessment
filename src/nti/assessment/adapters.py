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

from .interfaces import IQAggregatedPartFactory
from .interfaces import IQPartResponseNormalizer
from .interfaces import IQNonGradableMatchingPart
from .interfaces import IQNonGradableOrderingPart
from .interfaces import IQNonGradableFreeResponsePart
from .interfaces import IQNonGradableModeledContentPart
from .interfaces import IQNonGradableMultipleChoicePart
from .interfaces import IQMatchingPartResponseNormalizer
from .interfaces import IQOrderingPartResponseNormalizer
from .interfaces import IQFreeResponsePartResponseNormalizer
from .interfaces import IQModeledContentPartResponseNormalizer
from .interfaces import IQMultipleChoicePartResponseNormalizer
from .interfaces import IQNonGradableMultipleChoiceMultipleAnswerPart
from .interfaces import IQMultipleChoiceMultipleAnswerPartResponseNormalizer

from .survey import QAggregatedMatchingPart
from .survey import QAggregatedOrderingPart
from .survey import QAggregatedFreeResponsePart
from .survey import QAggregatedModeledContentPart
from .survey import QAggregatedMultipleChoicePart
from .survey import QAggregatedMultipleChoiceMultipleAnswerPart

@interface.implementer(IQPartResponseNormalizer)
class AbstractResponseNormalizer(object):

	def __init__(self, part, response):
		self.part = part
		self.response = response

	def __call__(self):
		raise NotImplementedError()

@interface.implementer(IQMultipleChoicePartResponseNormalizer)
class MultipleChoicePartResponseNormalizer(AbstractResponseNormalizer):

	def __call__(self):
		index = None
		try:
			index = self.part.choices.index(self.response.value)
		except ValueError:
			# The value they sent isn't present. Maybe they sent an int string?
			try:
				index = int(self.response.value)
				# They sent an int. We can take this, if the actual value they sent
				# is not an option. If the choices are "0", "2", "3", with index 1, value "2"
				# being correct, and they send "1", we shouldn't accept that
				# TODO: Handle that case. Fortunately, it's a corner case
			except ValueError:
				# Nope, not an int. So this won't match
				index = None
		return index

@interface.implementer(IQMultipleChoiceMultipleAnswerPartResponseNormalizer)
class MultipleChoiceMultipleAnswerPartResponseNormalizer(AbstractResponseNormalizer):

	def __call__(self):
		if self.response.value:
			result = tuple(sorted(self.response.value))
		else:
			result = ()
		return result

@interface.implementer(IQFreeResponsePartResponseNormalizer)
class FreeResponsePartResponseNormalizer(AbstractResponseNormalizer):

	def __call__(self):
		result = self.response.value.lower() if self.response.value else u''
		return result

@interface.implementer(IQModeledContentPartResponseNormalizer)
class ModeledContentPartResponseNormalizer(AbstractResponseNormalizer):

	def __call__(self):
		result = self.response.value if self.response.value else u''
		return result

class ConnectingPartResponseNormalizer(AbstractResponseNormalizer):

	def __call__(self):
		result = self.response.value if self.response.value is not None else None
		return result
	
@interface.implementer(IQMatchingPartResponseNormalizer)
class MatchingPartResponseNormalizer(ConnectingPartResponseNormalizer):
	pass

@interface.implementer(IQOrderingPartResponseNormalizer)
class OrderingPartResponseNormalizer(ConnectingPartResponseNormalizer):
	pass

@interface.implementer(IQAggregatedPartFactory)
@component.adapter(IQNonGradableFreeResponsePart)
def NonGradableFreeResponsePartFactory(part):
	return QAggregatedFreeResponsePart

@interface.implementer(IQAggregatedPartFactory)
@component.adapter(IQNonGradableModeledContentPart)
def NonGradableModeledContentPartFactory(part):
	return QAggregatedModeledContentPart

@interface.implementer(IQAggregatedPartFactory)
@component.adapter(IQNonGradableMultipleChoicePart)
def NonGradableMultipleChoicePartFactory(part):
	return QAggregatedMultipleChoicePart

@interface.implementer(IQAggregatedPartFactory)
@component.adapter(IQNonGradableMultipleChoiceMultipleAnswerPart)
def NonGradableMultipleChoiceMultipleAnswerPartFactory(part):
	return QAggregatedMultipleChoiceMultipleAnswerPart

@interface.implementer(IQAggregatedPartFactory)
@component.adapter(IQNonGradableMatchingPart)
def NonGradableMatchingPartFactory(part):
	return QAggregatedMatchingPart

@interface.implementer(IQAggregatedPartFactory)
@component.adapter(IQNonGradableOrderingPart)
def NonGradableOrderingPartFactory(part):
	return QAggregatedOrderingPart
