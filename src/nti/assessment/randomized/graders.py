#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.assessment.graders import EqualityGrader
from nti.assessment.graders import ConnectingPartGrader
from nti.assessment.graders import MultipleChoiceMultipleAnswerGrader

from nti.assessment.randomized import randomize
from nti.assessment.randomized import shuffle_list

from nti.assessment.randomized.interfaces import IQRandomizedMatchingPartGrader
from nti.assessment.randomized.interfaces import IQRandomizedOrderingPartGrader
from nti.assessment.randomized.interfaces import IQRandomizedMultipleChoicePartGrader
from nti.assessment.randomized.interfaces import IRandomizedPartGraderUnshuffleValidator
from nti.assessment.randomized.interfaces import IQRandomizedMultipleChoiceMultipleAnswerPartGrader

logger = __import__('logging').getLogger(__name__)


def _needs_unshuffled(grader, creator):
    """
    Check if our response should be unshuffled (only for students).
    """
    utility = component.queryUtility(IRandomizedPartGraderUnshuffleValidator)
    question = grader.part.question
    return utility is None or utility.needs_unshuffled(question, creator)


class RandomizedConnectingPartGrader(ConnectingPartGrader):

    def unshuffle(self, the_dict, user=None, context=None):
        user = user if user else self.creator
        the_dict = {k: int(v) for k, v in the_dict.items()}
        the_dict = ConnectingPartGrader._to_int_dict(self, the_dict)
        if not _needs_unshuffled(self, user):
            return the_dict
        generator = randomize(user=user, context=context)
        if generator is not None:
            values = list(self.part.values)
            original = {v: idx for idx, v in enumerate(values)}
            shuffled = {
				idx: v for idx, v in enumerate(shuffle_list(generator, values))
			}
            for k in list(the_dict):
                idx = the_dict[k]
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
        the_value = int(the_value)
        user = user if user else self.creator
        if not _needs_unshuffled(self, user):
            return the_value
        generator = randomize(user=user, context=context)
        if generator is not None:
            choices = list(self.part.choices)
            original = {v: idx for idx, v in enumerate(choices)}
            shuffled = {
				idx: v for idx, v in enumerate(shuffle_list(generator, choices))
			}
            the_value = original[shuffled[the_value]]
        return the_value

    response_converter = unshuffle


@interface.implementer(IQRandomizedMultipleChoiceMultipleAnswerPartGrader)
class RandomizedMultipleChoiceMultipleAnswerGrader(MultipleChoiceMultipleAnswerGrader):

    def unshuffle(self, the_values, user=None, context=None):
        user = user if user else self.creator
        the_values = sorted([int(x) for x in the_values])
        if not _needs_unshuffled(self, user):
            return the_values
        generator = randomize(user=user, context=context)
        if generator is not None:
            choices = list(self.part.choices)
            original = {v: idx for idx, v in enumerate(choices)}
            shuffled = {
				idx: v for idx, v in enumerate(shuffle_list(generator, choices))
			}
            for pos, idx in enumerate(the_values):
                uidx = original[shuffled[idx]]
                the_values[pos] = uidx
            the_values = sorted(the_values)
        return the_values
    response_converter = unshuffle
