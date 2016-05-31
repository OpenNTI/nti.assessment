#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.assessment.interfaces import IQPartSolutionsExternalizer

from nti.assessment.randomized import randomize
from nti.assessment.randomized import must_randomize
from nti.assessment.randomized import shuffle_matching_part_solutions
from nti.assessment.randomized import shuffle_multiple_choice_part_solutions
from nti.assessment.randomized import shuffle_multiple_choice_multiple_answer_part_solutions

from nti.assessment.randomized.interfaces import IQRandomizedMatchingPart
from nti.assessment.randomized.interfaces import IQRandomizedOrderingPart
from nti.assessment.randomized.interfaces import IQRandomizedMultipleChoicePart
from nti.assessment.randomized.interfaces import IQRandomizedMultipleChoiceMultipleAnswerPart

from nti.externalization.externalization import to_external_object

@interface.implementer(IQPartSolutionsExternalizer)
@component.adapter(IQRandomizedMatchingPart)
class _RandomizedMatchingPartSolutionsExternalizer(object):

	__slots__ = ('part',)

	def __init__(self, part):
		self.part = part

	def to_external_object(self):
		# CS: 20150815 make sure we skip the externalization cache
		# since this method may be called from a decorator and the state
		# cache may have been set
		solutions = to_external_object(self.part.solutions, useCache=False)
		if must_randomize(self.part):
			generator = randomize(context=self.part)
			if generator is not None:
				values = to_external_object(self.part.values, useCache=False)
				shuffle_matching_part_solutions(generator, values, solutions)
		return solutions

@interface.implementer(IQPartSolutionsExternalizer)
@component.adapter(IQRandomizedOrderingPart)
class _RandomizedOrderingPartSolutionsExternalizer(_RandomizedMatchingPartSolutionsExternalizer):
	pass

@interface.implementer(IQPartSolutionsExternalizer)
@component.adapter(IQRandomizedMultipleChoicePart)
class _RandomizedMultipleChoicePartSolutionsExternalizer(object):

	__slots__ = ('part',)

	def __init__(self, part):
		self.part = part

	def to_external_object(self):
		solutions = to_external_object(self.part.solutions, useCache=False)
		if must_randomize(self.part):
			generator = randomize(context=self.part)
			if generator is not None:
				choices = to_external_object(self.part.choices, useCache=False)
				shuffle_multiple_choice_part_solutions(generator, choices, solutions)
		return solutions

@interface.implementer(IQPartSolutionsExternalizer)
@component.adapter(IQRandomizedMultipleChoiceMultipleAnswerPart)
class _RandomizedMultipleChoiceMultipleAnswerPartSolutionsExternalizer(object):

	__slots__ = ('part',)

	def __init__(self, part):
		self.part = part

	def to_external_object(self):
		solutions = to_external_object(self.part.solutions, useCache=False)
		if must_randomize(self.part):
			generator = randomize(context=self.part)
			if generator is not None:
				choices = to_external_object(self.part.choices, useCache=False)
				shuffle_multiple_choice_multiple_answer_part_solutions(generator, choices, solutions)
		return solutions
