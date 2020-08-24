#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from hamcrest import is_
from hamcrest import assert_that
from hamcrest import instance_of

from zope import interface

from nti.assessment.randomized.interfaces import IQRandomizedPart
from nti.assessment.randomized.interfaces import IRandomizedPartsContainer

from nti.assessment.parts import QMultipleChoicePart

from nti.assessment.question import QQuestion
from nti.assessment.question import QQuestionSet

from nti.assessment.randomized_proxy import RandomizedPartProxy
from nti.assessment.randomized_proxy import QuestionRandomizedPartsProxy

from nti.assessment.solution import QMultipleChoiceSolution

from nti.assessment.tests import AssessmentTestCase

class TestRandomizedProxy(AssessmentTestCase):
    """
    Tests validating randomized proxy functionality, specifically when
    acquiring questions from marked question sets.
    """

    def test_proxy(self):
        part = QMultipleChoicePart(solutions=(QMultipleChoiceSolution(value=1),))
        question = QQuestion(parts=(part,))
        question_set = QQuestionSet(questions=(question,))

        interface.alsoProvides(question_set, IRandomizedPartsContainer)
        for found_question in (tuple(question_set.Items)[0],
                               question_set[0]):
            assert_that(found_question, instance_of(QuestionRandomizedPartsProxy))
            for found_part in (found_question.parts[0],
                               found_question[0]):
                assert_that(found_part, instance_of(RandomizedPartProxy))
                assert_that(found_part.randomized, is_(True))
                assert_that(IQRandomizedPart.providedBy(found_part), is_(True))

