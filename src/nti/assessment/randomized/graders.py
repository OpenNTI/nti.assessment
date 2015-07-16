#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from . import randomize
from . import shuffle_list

from ..graders import EqualityGrader
from ..graders import ConnectingPartGrader
from ..graders import MultipleChoiceMultipleAnswerGrader

from .interfaces import IQRandomizedMatchingPartGrader
from .interfaces import IQRandomizedOrderingPartGrader
from .interfaces import IQRandomizedMultipleChoicePartGrader
from .interfaces import IQRandomizedMultipleChoiceMultipleAnswerPartGrader

class RandomizedConnectingPartGrader(ConnectingPartGrader):

	def unshuffle(self, the_dict, user=None, context=None):
		the_dict = ConnectingPartGrader._to_int_dict(self, the_dict)
		generator = randomize(user=user, context=context)
		if generator is not None:
			values = list(self.part.values)
			original = {v:idx for idx, v in enumerate(values)}
			shuffled = {idx:v for idx, v in enumerate(shuffle_list(generator, values))}
			for k in list(the_dict.keys()):
				idx = int(the_dict[k])
				uidx = original.get(shuffled.get(idx), idx)
				the_dict[k] = uidx
		return the_dict

	response_converter = _to_response_dict = unshuffle

@interface.implementer(IQRandomizedMatchingPartGrader)
class RandomizedMatchingPartGrader(RandomizedConnectingPartGrader):
	pass

@interface.implementer(IQRandomizedOrderingPartGrader)
class RandomizedOrderingPartGrader(RandomizedConnectingPartGrader):
	pass

@interface.implementer(IQRandomizedMultipleChoicePartGrader)
class RandomizedMultipleChoiceGrader(EqualityGrader):

	# MultipleChoiceGrader tries really hard to verify correctness,
	# when we just need something simple. Thus, we inherit from EqualityGrader.

	def __call__(self):
		if hasattr(self.response, 'value'):
			return self._compare(self.solution.value, self.response.value)
		else:
			return self._compare(self.solution.value, self.response)

	def unshuffle(self, the_value, user=None, context=None):
		generator = randomize(user=user, context=context)
		if generator is not None:
			the_value = int(the_value)
			choices = list(self.part.choices)
			original = {v:idx for idx, v in enumerate(choices)}
			shuffled = {idx:v for idx, v in enumerate(shuffle_list(generator, choices))}
			the_value = original[shuffled[the_value]]
		return the_value

	response_converter = unshuffle

@interface.implementer(IQRandomizedMultipleChoiceMultipleAnswerPartGrader)
class RandomizedMultipleChoiceMultipleAnswerGrader(MultipleChoiceMultipleAnswerGrader):

	def unshuffle(self, the_values, user=None, context=None):
		generator = randomize(user=user, context=context)
		if generator is not None:
			the_values = list(the_values)
			choices = list(self.part.choices)
			original = {v:idx for idx, v in enumerate(choices)}
			shuffled = {idx:v for idx, v in enumerate(shuffle_list(generator, choices))}
			for pos, value in enumerate(the_values):
				idx = int(value)
				uidx = original[shuffled[idx]]
				the_values[pos] = uidx
			the_values = sorted(the_values)
		return the_values

	response_converter = unshuffle
