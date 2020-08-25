#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
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


class TestQuestionSet(AssessmentTestCase):

    def test_question_set(self):
        """
        Test question set interaction, mainly around result wrapper.
        """
        part = QMultipleChoicePart(solutions=(QMultipleChoiceSolution(value=1),))
        question = QQuestion(parts=(part,))
        ntiid = u'tag:nextthought.com,2015-11-30:Test'
        question.ntiid = ntiid
        question_set = QQuestionSet(questions=(question,))

        question2 = QQuestion(parts=(part,))
        ntiid2 = u'tag:nextthought.com,2015-11-30:Test2'
        question2.ntiid = ntiid2

        # Cannot modify directly
        with self.assertRaises(AttributeError):
            question_set.questions.append(question)
        with self.assertRaises(TypeError):
            question_set.questions[0] = question

        # Interacting via interface
        assert_that(tuple(question_set.Items)[0], is_(question))
        assert_that(question_set.questions[0], is_(question))
        assert_that(question_set.get_question_by_ntiid(ntiid),
                    is_(question))
        assert_that(question_set.get_question_by_ntiid('dne:ntiid'),
                    none())
        assert_that(question_set.pop(0), is_(question))

        # Empty case
        assert_that(len(question_set), is_(0))
        assert_that(len(question_set.questions), is_(0))
        assert_that(len(tuple(question_set.Items)), is_(0))
        assert_that(question_set.get_question_by_ntiid('dne:ntiid'),
                    none())

        # Insert and multiple case
        question_set.append(question)
        assert_that(len(question_set), is_(1))
        question_set.insert(0, question2)
        assert_that(len(question_set), is_(2))

        assert_that(tuple(question_set.Items)[0], is_(question2))
        assert_that(question_set.questions[0], is_(question2))
        assert_that(question_set.questions[1], is_(question))
        assert_that(question_set.get_question_by_ntiid(ntiid),
                    is_(question))
        assert_that(question_set.get_question_by_ntiid(ntiid2),
                    is_(question2))
        assert_that(question_set.get_question_by_ntiid('dne:ntiid'),
                    none())
        assert_that(question_set.pop(0), is_(question2))
        assert_that(question_set.remove(question), is_(question))

    def test_proxy(self):
        """
        Tests validating randomized proxy functionality, specifically when
        acquiring questions from marked question sets.
        """
        part = QMultipleChoicePart(solutions=(QMultipleChoiceSolution(value=1),))
        question = QQuestion(parts=(part,))
        question_set = QQuestionSet(questions=(question,))

        def check_elements(randomized=False):
            rand_check = is_ if randomized else is_not
            for found_question in (tuple(question_set.Items)[0],
                                   question_set.questions[0],
                                   question_set[0]):
                assert_that(found_question, rand_check(instance_of(QuestionRandomizedPartsProxy)))
                for found_part in (found_question.parts[0],
                                   found_question[0]):
                    assert_that(found_part,
                                rand_check(instance_of(RandomizedPartProxy)))
                    assert_that(found_part.randomized, is_(randomized))
                    assert_that(IQRandomizedPart.providedBy(found_part),
                                is_(randomized))

        check_elements(randomized=False)
        interface.alsoProvides(question_set, IRandomizedPartsContainer)
        check_elements(randomized=True)
        interface.noLongerProvides(question_set, IRandomizedPartsContainer)
        check_elements(randomized=False)
