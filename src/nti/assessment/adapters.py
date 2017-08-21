#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.assessment.interfaces import IQAggregatedPartFactory
from nti.assessment.interfaces import IQPartResponseNormalizer
from nti.assessment.interfaces import IQNonGradableMatchingPart
from nti.assessment.interfaces import IQNonGradableOrderingPart
from nti.assessment.interfaces import IQNonGradableFreeResponsePart
from nti.assessment.interfaces import IQNonGradableModeledContentPart
from nti.assessment.interfaces import IQNonGradableMultipleChoicePart
from nti.assessment.interfaces import IQMatchingPartResponseNormalizer
from nti.assessment.interfaces import IQOrderingPartResponseNormalizer
from nti.assessment.interfaces import IQFreeResponsePartResponseNormalizer
from nti.assessment.interfaces import IQModeledContentPartResponseNormalizer
from nti.assessment.interfaces import IQMultipleChoicePartResponseNormalizer
from nti.assessment.interfaces import IQNonGradableMultipleChoiceMultipleAnswerPart
from nti.assessment.interfaces import IQMultipleChoiceMultipleAnswerPartResponseNormalizer

from nti.assessment.survey import QAggregatedMatchingPart
from nti.assessment.survey import QAggregatedOrderingPart
from nti.assessment.survey import QAggregatedFreeResponsePart
from nti.assessment.survey import QAggregatedModeledContentPart
from nti.assessment.survey import QAggregatedMultipleChoicePart
from nti.assessment.survey import QAggregatedMultipleChoiceMultipleAnswerPart


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
        result = self.response.value.lower() if self.response.value else None
        return result


@interface.implementer(IQModeledContentPartResponseNormalizer)
class ModeledContentPartResponseNormalizer(AbstractResponseNormalizer):

    def __call__(self):
        result = self.response.value if self.response.value else None
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
def NonGradableFreeResponsePartFactory(_):
    return QAggregatedFreeResponsePart


@interface.implementer(IQAggregatedPartFactory)
@component.adapter(IQNonGradableModeledContentPart)
def NonGradableModeledContentPartFactory(_):
    return QAggregatedModeledContentPart


@interface.implementer(IQAggregatedPartFactory)
@component.adapter(IQNonGradableMultipleChoicePart)
def NonGradableMultipleChoicePartFactory(_):
    return QAggregatedMultipleChoicePart


@interface.implementer(IQAggregatedPartFactory)
@component.adapter(IQNonGradableMultipleChoiceMultipleAnswerPart)
def NonGradableMultipleChoiceMultipleAnswerPartFactory(_):
    return QAggregatedMultipleChoiceMultipleAnswerPart


@interface.implementer(IQAggregatedPartFactory)
@component.adapter(IQNonGradableMatchingPart)
def NonGradableMatchingPartFactory(_):
    return QAggregatedMatchingPart


@interface.implementer(IQAggregatedPartFactory)
@component.adapter(IQNonGradableOrderingPart)
def NonGradableOrderingPartFactory(_):
    return QAggregatedOrderingPart
