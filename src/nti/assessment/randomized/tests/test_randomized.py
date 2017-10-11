#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_not
from hamcrest import not_none
from hamcrest import equal_to
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import same_instance
does_not = is_not

import os
import json
import fudge

from nti.assessment.randomized import randomize
from nti.assessment.randomized import shuffle_list
from nti.assessment.randomized import questionbank_question_chooser

from nti.assessment.randomized.interfaces import IQRandomizedPart
from nti.assessment.randomized.interfaces import IQuestionIndexRange

from nti.externalization import internalization

from nti.assessment.tests import AssessmentTestCase


class TestRandomized(AssessmentTestCase):

    @fudge.patch('nti.assessment.randomized.get_seed')
    def test_randomize(self, mock_gs):
        mock_gs.is_callable().with_args().returns(100)

        size = 20
        ichigo = 'ichigo@nti.com'
        numbers_1 = range(0, size)
        generator = randomize(ichigo)
        shuffle_list(generator, numbers_1)

        numbers_2 = range(0, size)
        generator = randomize(ichigo)
        shuffle_list(generator, numbers_2)

        assert_that(numbers_1, is_(numbers_2))

        mock_gs.is_callable().with_args().returns(500)
        aizen = 'aizen@nti.com'
        numbers_3 = range(0, size)
        generator = randomize(aizen)
        shuffle_list(generator, numbers_3)

        assert_that(numbers_1, is_not(numbers_3))

    @fudge.patch('nti.assessment.randomized.get_seed')
    def test_question_bank_1(self, mock_gs):

        path = os.path.join(os.path.dirname(__file__), "question_bank_1.json")
        with open(path, "r") as fp:
            ext_obj = json.load(fp)

        factory = internalization.find_factory_for(ext_obj)
        assert_that(factory, is_(not_none()))

        internal = factory()
        internalization.update_from_external_object(internal, ext_obj,
                                                    require_updater=True)

        questions = internal.questions
        assert_that(questions, has_length(20))
        assert_that(IQRandomizedPart.providedBy(questions[1].parts[0]), 
                    is_(True))

        user1 = 'user1@nti.com'
        mock_gs.is_callable().with_args().returns(100)
        questions = questionbank_question_chooser(internal, user=user1)
        assert_that(questions, has_length(internal.draw))

        user2 = 'user2@nti.com'
        mock_gs.is_callable().with_args().returns(500)
        questions2 = questionbank_question_chooser(internal, user=user2)
        assert_that(questions, is_not(equal_to(questions2)))

        internal.draw = 2
        mock_gs.is_callable().with_args().returns(100)
        internal.ranges = [
            IQuestionIndexRange([0, 5]), 
            IQuestionIndexRange([6, 10])
        ]
        questions = questionbank_question_chooser(internal, user=user1)
        assert_that(questions, has_length(internal.draw))

        mock_gs.is_callable().with_args().returns(500)
        questions2 = questionbank_question_chooser(internal, user=user2)
        assert_that(questions, is_not(equal_to(questions2)))

    @fudge.patch('nti.assessment.randomized.get_seed')
    def test_question_bank_2(self, mock_gs):

        path = os.path.join(os.path.dirname(__file__), "question_bank_2.json")
        with open(path, "r") as fp:
            ext_obj = json.load(fp)

        factory = internalization.find_factory_for(ext_obj)
        assert_that(factory, is_(not_none()))

        internal = factory()
        internalization.update_from_external_object(internal, ext_obj,
                                                    require_updater=True)

        user1 = 'user1@nti.com'
        mock_gs.is_callable().with_args().returns(100)
        questions_1 = questionbank_question_chooser(internal, user=user1)
        assert_that(questions_1, has_length(internal.draw))

        user2 = 'user2@nti.com'
        mock_gs.is_callable().with_args().returns(500)
        questions_2 = questionbank_question_chooser(internal, user=user2)
        assert_that(questions_2, has_length(internal.draw))

        assert_that(questions_1[-1], is_(same_instance(questions_2[-1])))
        assert_that(questions_1[0:-1], is_not(equal_to(questions_2[0:-1])))
