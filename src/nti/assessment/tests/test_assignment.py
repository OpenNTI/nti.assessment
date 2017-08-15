#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_not
from hamcrest import not_none
from hamcrest import has_item
from hamcrest import has_entry
from hamcrest import has_entries
from hamcrest import assert_that
from hamcrest import has_property
does_not = is_not

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

from nti.assessment import parts
from nti.assessment import question
from nti.assessment import assignment
from nti.assessment import interfaces

from nti.assessment.tests import AssessmentTestCase

from nti.externalization.tests import externalizes


class TestAssignment(AssessmentTestCase):

    def test_externalizes(self):
        assert_that(assignment.QAssignmentPart(),
                    verifiably_provides(interfaces.IQAssignmentPart))
        # But missing a question set
        assert_that(assignment.QAssignmentPart(),
                    does_not(validly_provides(interfaces.IQAssignmentPart)))

        assert_that(assignment.QAssignmentPart(),
                    externalizes(has_entry('Class', 'AssignmentPart')))

        questions = [question.QQuestion(parts=[parts.QMathPart()])]
        question_set = question.QQuestionSet(questions=questions)
        part = assignment.QAssignmentPart(question_set=question_set)
        assert_that(part, validly_provides(interfaces.IQAssignmentPart))

        assign_obj = assignment.QAssignment()
        assign_obj.title = u'title'
        assert_that(assign_obj, verifiably_provides(interfaces.IQAssignment))

        # This is now valid since we default to empty parts.
        assert_that(assign_obj, validly_provides(interfaces.IQAssignment))
        assert_that(assign_obj, externalizes(has_entries('Class', 'Assignment',
                                                         'category_name', 'default',
                                                         'CategoryName', 'default',
                                                         'no_submit', False,
                                                         'NoSubmit', False)))
        assert_that(assign_obj, externalizes(does_not(has_item('version'))))

        assign_obj.update_version()
        assert_that(assign_obj, externalizes(has_entry('version', not_none())))

        assert_that(assignment.QAssignment(parts=[part], title=u'title'),
                    validly_provides(interfaces.IQAssignment))

        assert_that(assignment.QAssignmentSubmissionPendingAssessment(),
                    verifiably_provides(interfaces.IQAssignmentSubmissionPendingAssessment))

        assert_that(assignment.QAssignmentSubmissionPendingAssessment(),
                    externalizes(has_entry('Class', 'AssignmentSubmissionPendingAssessment')))

    def test_props(self):
        assign_obj = assignment.QAssignment()
        assign_obj.ntiid = u'tag:nextthought.com,2011-10:OU-NAQ-quiz1'
        assert_that(assign_obj,
                    has_property('ntiid', 'tag:nextthought.com,2011-10:OU-NAQ-quiz1'))
        assert_that(assign_obj,
                    has_property('__name__', 'tag:nextthought.com,2011-10:OU-NAQ-quiz1'))
