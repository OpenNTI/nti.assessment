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

from nti.externalization.singleton import SingletonDecorator
from nti.externalization.externalization import to_external_object
from nti.externalization.interfaces import IExternalObjectDecorator

from ..interfaces import IQPartSolutionsExternalizer

from .interfaces import IQuestionBank
from .interfaces import IRandomizedQuestionSet
from .interfaces import IQRandomizedMatchingPart
from .interfaces import IQRandomizedOrderingPart
from .interfaces import IQRandomizedMultipleChoicePart
from .interfaces import IQRandomizedMultipleChoiceMultipleAnswerPart

from . import randomize
from . import shuffle_list
from . import questionbank_question_chooser

def _must_randomized(context):
	iface = getattr(context, 'nonrandomized_interface', None)
	return iface is None or not iface.providedBy(context)

# === matching

def _shuffle_matching_part_solutions(generator, values, ext_solutions):
	original = {idx:v for idx, v in enumerate(values)}
	shuffled = {v:idx for idx, v in enumerate(shuffle_list(generator, values))}
	for solution in ext_solutions:
		value = solution['value']
		for k in list(value.keys()):
			idx = int(value[k])
			uidx = shuffled[original[idx]]
			value[k] = uidx

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
		if _must_randomized(self.part):
			generator = randomize(context=self.part)
			if generator is not None:
				values = to_external_object(self.part.values, useCache=False)
				_shuffle_matching_part_solutions(generator, values, solutions)
		return solutions

@interface.implementer(IExternalObjectDecorator)
@component.adapter(IQRandomizedMatchingPart)
class _QRandomizedMatchingPartDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, context, result):
		if _must_randomized(context):
			generator = randomize(context=context)
			if generator is not None:
				values = list(result['values'])
				shuffle_list(generator, result['values'])
				_shuffle_matching_part_solutions(randomize(context=context), # new generator
												 values,
												 result['solutions'])

# === ordering

@interface.implementer(IQPartSolutionsExternalizer)
@component.adapter(IQRandomizedOrderingPart)
class _RandomizedOrderingPartSolutionsExternalizer(_RandomizedMatchingPartSolutionsExternalizer):
	pass

@interface.implementer(IExternalObjectDecorator)
@component.adapter(IQRandomizedOrderingPart)
class _QRandomizedOrderingPartDecorator(_QRandomizedMatchingPartDecorator):
	pass

# === multiple choice

def _shuffle_multiple_choice_part_solutions(generator, choices, ext_solutions):
	original = {idx:v for idx, v in enumerate(choices)}
	shuffled = {v:idx for idx, v in enumerate(shuffle_list(generator, choices))}
	for solution in ext_solutions:
		value = int(solution['value'])
		uidx = shuffled[original[value]]
		solution['value'] = uidx

@interface.implementer(IQPartSolutionsExternalizer)
@component.adapter(IQRandomizedMultipleChoicePart)
class _RandomizedMultipleChoicePartSolutionsExternalizer(object):

	__slots__ = ('part',)

	def __init__(self, part):
		self.part = part

	def to_external_object(self):
		solutions = to_external_object(self.part.solutions, useCache=False)
		if _must_randomized(self.part):
			generator = randomize(context=self.part)
			if generator is not None:
				choices = to_external_object(self.part.choices, useCache=False)
				_shuffle_multiple_choice_part_solutions(generator, choices, solutions)
		return solutions

@interface.implementer(IExternalObjectDecorator)
@component.adapter(IQRandomizedMultipleChoicePart)
class _QRandomizedMultipleChoicePartDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, context, result):
		if _must_randomized(context):
			generator = randomize(context=context)
			if generator is not None:
				solutions = result['solutions']
				choices = list(result['choices'])
				shuffle_list(generator, result['choices'])
				_shuffle_multiple_choice_part_solutions(randomize(context=context), #  new generator
														choices,
														solutions)

# === multiple choice, multiple answer part

def _shuffle_multiple_choice_multiple_answer_part_solutions(generator,
															choices,
															ext_solutions):
	original = {idx:v for idx, v in enumerate(choices)}
	shuffled = {v:idx for idx, v in enumerate(shuffle_list(generator, choices))}
	for solution in ext_solutions:
		value = solution['value']
		for pos, v in enumerate(value):
			idx = int(v)
			uidx = shuffled[original[idx]]
			value[pos] = uidx

@interface.implementer(IQPartSolutionsExternalizer)
@component.adapter(IQRandomizedMultipleChoiceMultipleAnswerPart)
class _RandomizedMultipleChoiceMultipleAnswerPartSolutionsExternalizer(object):

	__slots__ = ('part',)

	def __init__(self, part):
		self.part = part

	def to_external_object(self):
		solutions = to_external_object(self.part.solutions, useCache=False)
		if _must_randomized(self.part):
			generator = randomize(context=self.part)
			if generator is not None:
				choices = to_external_object(self.part.choices, useCache=False)
				_shuffle_multiple_choice_multiple_answer_part_solutions(generator,
																		choices,
																		solutions)
		return solutions

@interface.implementer(IExternalObjectDecorator)
@component.adapter(IQRandomizedMultipleChoiceMultipleAnswerPart)
class _QRandomizedMultipleChoiceMultipleAnswerPartDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, context, result):
		if _must_randomized(context):
			generator = randomize(context=context)
			if generator is not None:
				choices = list(result['choices'])
				shuffle_list(generator, result['choices'])
				_shuffle_multiple_choice_multiple_answer_part_solutions(randomize(context=context), #  new generator
																		choices,
																		result['solutions'])

# === question set

@interface.implementer(IExternalObjectDecorator)
@component.adapter(IRandomizedQuestionSet)
class _QRandomizedQuestionSetDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, context, result):
		if _must_randomized(context):
			generator = randomize(context=context)
			questions = result.get('questions', ())
			if generator and questions:
				shuffle_list(generator, questions)

@interface.implementer(IExternalObjectDecorator)
@component.adapter(IQuestionBank)
class _QQuestionBankDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, context, result):
		if _must_randomized(context):
			questions = result.get('questions', ())
			questions = questionbank_question_chooser(context, questions)
			result['questions'] = questions
