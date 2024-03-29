#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.assessment.interfaces import IQPart
from nti.assessment.interfaces import IQPartGrader
from nti.assessment.interfaces import IQuestionSet
from nti.assessment.interfaces import IQMatchingPart
from nti.assessment.interfaces import IQOrderingPart
from nti.assessment.interfaces import IQConnectingPart
from nti.assessment.interfaces import IQMatchingPartGrader
from nti.assessment.interfaces import IQOrderingPartGrader
from nti.assessment.interfaces import IQMultipleChoicePart
from nti.assessment.interfaces import IQMultipleChoicePartGrader
from nti.assessment.interfaces import IQMultipleChoiceMultipleAnswerPart
from nti.assessment.interfaces import IQMultipleChoiceMultipleAnswerPartGrader

from nti.schema.field import Int
from nti.schema.field import Object
from nti.schema.field import ListOrTuple

from nti.schema.jsonschema import TAG_HIDDEN_IN_UI
from nti.schema.jsonschema import TAG_REQUIRED_IN_UI

# marker


class ISha224Randomized(interface.Interface):
    """
    marker interface to use the following generator

    hexdigest = hashlib.sha224(bytes(uid)).hexdigest()
    generator = random.Random(long(hexdigest, 16))

    where uid is the user int id
    """
ISha224Randomized.setTaggedValue('_ext_is_marker_interface', True)

# parts


class IQRandomizedPart(IQPart):
    """
    marker interface for randomized parts
    """
IQRandomizedPart.setTaggedValue('_ext_is_marker_interface', True)


class ISha224RandomizedPart(IQRandomizedPart, ISha224Randomized):
    """
    marker interface for randomized parts that use Sha224 algorithm
    """
ISha224RandomizedPart.setTaggedValue('_ext_is_marker_interface', True)


class IQRandomizedPartGrader(IQPartGrader):

    def unshuffle(value, user=None, context=None, seed=None):
        """
        unrandomize the specified value
        """


# connecting part


class IQRandomizedConnectingPart(IQRandomizedPart, IQConnectingPart):
    pass


class ISha224RandomizedConnectingPart(IQRandomizedConnectingPart, ISha224Randomized):
    pass


# matching part


class IQRandomizedMatchingPart(IQRandomizedConnectingPart, IQMatchingPart):
    pass


class IQRandomizedMatchingPartGrader(IQMatchingPartGrader, IQRandomizedPartGrader):
    pass


class ISha224RandomizedMatchingPart(IQRandomizedMatchingPart, ISha224RandomizedPart):
    pass


# ordering


class IQRandomizedOrderingPart(IQRandomizedConnectingPart, IQOrderingPart):
    pass


class IQRandomizedOrderingPartGrader(IQOrderingPartGrader, IQRandomizedPartGrader):
    pass


class ISha224RandomizedOrderingPart(IQRandomizedOrderingPart, ISha224RandomizedPart):
    pass


# multiple choice


class IQRandomizedMultipleChoicePart(IQRandomizedPart, IQMultipleChoicePart):
    pass


class IQRandomizedMultipleChoicePartGrader(IQMultipleChoicePartGrader, IQRandomizedPartGrader):
    pass


class ISha224RandomizedMultipleChoicePart(IQRandomizedMultipleChoicePart, ISha224RandomizedPart):
    pass

# multiple choice, multiple answer


class IQRandomizedMultipleChoiceMultipleAnswerPart(IQRandomizedPart,
                                                   IQMultipleChoiceMultipleAnswerPart):
    pass


class IQRandomizedMultipleChoiceMultipleAnswerPartGrader(IQMultipleChoiceMultipleAnswerPartGrader,
                                                         IQRandomizedPartGrader):
    pass


class ISha224RandomizedMultipleChoiceMultipleAnswerPart(IQRandomizedMultipleChoiceMultipleAnswerPart,
                                                        ISha224RandomizedPart):
    pass


# question set


class IRandomizedQuestionSet(IQuestionSet):
    """
    A marker interface that indicates this IQuestionSet contains questions
    in random order.
    """
IRandomizedQuestionSet.setTaggedValue('__external_class_name__', "QuestionSet")


class IRandomizedPartsContainer(interface.Interface):
    """
    A marker interface that indicates the underlying `IQParts` should
    *all* be treated as randomized.
    """
IRandomizedPartsContainer.setTaggedValue('_ext_is_marker_interface', True)


# question bank


class IQuestionIndexRange(interface.Interface):
    start = Int(title=u"start index range", min=0, required=True)
    end = Int(title=u"end index range", min=0, required=True)
    draw = Int(title=u"number of questions to draw in range",
			   min=1,
			   required=True,
               default=1)


class IQuestionBank(IQuestionSet):
    """
    An group of questions taken at random

    A maximum total of questions of the question set is drawn to be presented and evaluated.
    """

    draw = Int(title=u"number of questions to be randomly drawn", min=1,
               required=True, default=1)

    ranges = ListOrTuple(Object(IQuestionIndexRange), title=u"Question index ranges",
                         required=False, default=())

    def copy(questions=None, ranges=None):
        """
        Copy this question bank

        :param questions: Questions to add to this bank
        :param ranges: Question bank ranges
        """

IQuestionBank['draw'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQuestionBank['draw'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQuestionBank['ranges'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQuestionBank['ranges'].setTaggedValue(TAG_REQUIRED_IN_UI, False)


# Principal utility


class IPrincipalSeedSelector(interface.Interface):
    """
    Defines a utility function to return a random seed for a pricipal
    """

    def __call__(principal):
        """
        return a random seed for the specified principal
        """


class IRandomizedPartGraderUnshuffleValidator(interface.Interface):
    """
    Determines if the randomized grader part needs to unshuffle
    the incoming submission values.
    """

    def needs_unshuffled(context, creator):
        """
        returns True if the given part context needs to be unshuffled.
        """
    needsUnshuffled = needs_unshuffled
