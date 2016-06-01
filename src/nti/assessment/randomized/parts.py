#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.assessment.parts import QMatchingPart
from nti.assessment.parts import QOrderingPart
from nti.assessment.parts import QConnectingPart
from nti.assessment.parts import QMultipleChoicePart
from nti.assessment.parts import QMultipleChoiceMultipleAnswerPart

from nti.assessment.randomized.interfaces import ISha224RandomizedMatchingPart
from nti.assessment.randomized.interfaces import ISha224RandomizedOrderingPart
from nti.assessment.randomized.interfaces import ISha224RandomizedMultipleChoicePart
from nti.assessment.randomized.interfaces import ISha224RandomizedMultipleChoiceMultipleAnswerPart

from nti.assessment.randomized.interfaces import IQRandomizedMatchingPart
from nti.assessment.randomized.interfaces import IQRandomizedOrderingPart
from nti.assessment.randomized.interfaces import INonRandomizedMatchingPart
from nti.assessment.randomized.interfaces import INonRandomizedOrderingPart
from nti.assessment.randomized.interfaces import IQRandomizedConnectingPart
from nti.assessment.randomized.interfaces import IQRandomizedMatchingPartGrader
from nti.assessment.randomized.interfaces import IQRandomizedOrderingPartGrader
from nti.assessment.randomized.interfaces import IQRandomizedMultipleChoicePart
from nti.assessment.randomized.interfaces import INonRandomizedMultipleChoicePart
from nti.assessment.randomized.interfaces import IQRandomizedMultipleChoicePartGrader
from nti.assessment.randomized.interfaces import IQRandomizedMultipleChoiceMultipleAnswerPart
from nti.assessment.randomized.interfaces import INonRandomizedMultipleChoiceMultipleAnswerPart
from nti.assessment.randomized.interfaces import IQRandomizedMultipleChoiceMultipleAnswerPartGrader

@interface.implementer(IQRandomizedConnectingPart)
class QRandomizedConnectingPart(QConnectingPart):
	response_interface = None

@interface.implementer(IQRandomizedMatchingPart)
class QRandomizedMatchingPart(QRandomizedConnectingPart, QMatchingPart):

	response_interface = None

	__external_class_name__ = "MatchingPart"
	mimeType = mime_type = "application/vnd.nextthought.assessment.randomizedmatchingpart"

	grader_interface = IQRandomizedMatchingPartGrader

	nonrandomized_interface = INonRandomizedMatchingPart
	sha224randomized_interface = ISha224RandomizedMatchingPart

@interface.implementer(IQRandomizedOrderingPart)
class QRandomizedOrderingPart(QRandomizedConnectingPart, QOrderingPart):

	__external_class_name__ = "OrderingPart"
	mimeType = mime_type = "application/vnd.nextthought.assessment.randomizedorderingpart"

	grader_interface = IQRandomizedOrderingPartGrader

	nonrandomized_interface = INonRandomizedOrderingPart
	sha224randomized_interface = ISha224RandomizedOrderingPart

@interface.implementer(IQRandomizedMultipleChoicePart)
class QRandomizedMultipleChoicePart(QMultipleChoicePart):

	response_interface = None

	__external_class_name__ = "MultipleChoicePart"
	mimeType = mime_type = "application/vnd.nextthought.assessment.randomizedmultiplechoicepart"

	grader_interface = IQRandomizedMultipleChoicePartGrader

	nonrandomized_interface = INonRandomizedMultipleChoicePart
	sha224randomized_interface = ISha224RandomizedMultipleChoicePart

@interface.implementer(IQRandomizedMultipleChoiceMultipleAnswerPart)
class QRandomizedMultipleChoiceMultipleAnswerPart(QMultipleChoiceMultipleAnswerPart):

	response_interface = None

	__external_class_name__ = "MultipleChoiceMultipleAnswerPart"
	mimeType = mime_type = "application/vnd.nextthought.assessment.randomizedmultiplechoicemultipleanswerpart"

	grader_interface = IQRandomizedMultipleChoiceMultipleAnswerPartGrader

	nonrandomized_interface = INonRandomizedMultipleChoiceMultipleAnswerPart
	sha224randomized_interface = ISha224RandomizedMultipleChoiceMultipleAnswerPart

def randomized_connecting_part_factory(ext_obj):
	def _factory():
		result = QConnectingPart()
		result.randomized = True
		return result
	return _factory

def randomized_matching_part_factory(ext_obj):
	def _factory():
		result = QMatchingPart()
		result.randomized = True
		return result
	return _factory

def randomized_ordering_part_factory(ext_obj):
	def _factory():
		result = QOrderingPart()
		result.randomized = True
		return result
	return _factory

def randomized_multiple_choice_part_factory(ext_obj):
	def _factory():
		result = QMultipleChoicePart()
		result.randomized = True
		return result
	return _factory

def randomized_multiple_choice_multiple_answer_part_factory(ext_obj):
	def _factory():
		result = QMultipleChoiceMultipleAnswerPart()
		result.randomized = True
		return result
	return _factory
