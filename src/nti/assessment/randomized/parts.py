#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.deprecation import deprecated

from nti.assessment.parts import QMatchingPart
from nti.assessment.parts import QOrderingPart
from nti.assessment.parts import QConnectingPart
from nti.assessment.parts import QMultipleChoicePart
from nti.assessment.parts import QMultipleChoiceMultipleAnswerPart

from nti.assessment.randomized.interfaces import IQRandomizedMatchingPart
from nti.assessment.randomized.interfaces import IQRandomizedOrderingPart
from nti.assessment.randomized.interfaces import IQRandomizedConnectingPart
from nti.assessment.randomized.interfaces import IQRandomizedMultipleChoicePart
from nti.assessment.randomized.interfaces import IQRandomizedMultipleChoiceMultipleAnswerPart

deprecated('QRandomizedConnectingPart', 'No longer used')
@interface.implementer(IQRandomizedConnectingPart)
class QRandomizedConnectingPart(QConnectingPart):
	pass

deprecated('QRandomizedMatchingPart', 'No longer used')
@interface.implementer(IQRandomizedMatchingPart)
class QRandomizedMatchingPart(QRandomizedConnectingPart, QMatchingPart):
	mimeType = mime_type = "application/vnd.nextthought.assessment.randomizedmatchingpart"

deprecated('QRandomizedOrderingPart', 'No longer used')
@interface.implementer(IQRandomizedOrderingPart)
class QRandomizedOrderingPart(QRandomizedConnectingPart, QOrderingPart):
	mimeType = mime_type = "application/vnd.nextthought.assessment.randomizedorderingpart"

deprecated('QRandomizedMultipleChoicePart', 'No longer used')
@interface.implementer(IQRandomizedMultipleChoicePart)
class QRandomizedMultipleChoicePart(QMultipleChoicePart):
	mimeType = mime_type = "application/vnd.nextthought.assessment.randomizedmultiplechoicepart"

deprecated('QRandomizedMultipleChoiceMultipleAnswerPart', 'No longer used')
@interface.implementer(IQRandomizedMultipleChoiceMultipleAnswerPart)
class QRandomizedMultipleChoiceMultipleAnswerPart(QMultipleChoiceMultipleAnswerPart):
	mimeType = mime_type = "application/vnd.nextthought.assessment.randomizedmultiplechoicemultipleanswerpart"

def _get_randomized_object( factory ):
	result = factory()
	result.randomized = True
	return result

def randomized_matching_part_factory(ext_obj):
	def _factory():
		return _get_randomized_object( QMatchingPart )
	return _factory

def randomized_ordering_part_factory(ext_obj):
	def _factory():
		return _get_randomized_object( QOrderingPart )
	return _factory

def randomized_multiple_choice_part_factory(ext_obj):
	def _factory():
		return _get_randomized_object( QMultipleChoicePart )
	return _factory

def randomized_multiple_choice_multiple_answer_part_factory(ext_obj):
	def _factory():
		return _get_randomized_object( QMultipleChoiceMultipleAnswerPart )
	return _factory
