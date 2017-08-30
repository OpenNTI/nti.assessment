#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_key
from hamcrest import contains
from hamcrest import not_none
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import greater_than
from hamcrest import has_property
from hamcrest import same_instance

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

from nose.tools import assert_raises

from zope.schema.interfaces import RequiredMissing
from zope.schema.interfaces import WrongContainedType

from nti.assessment.common import has_submitted_file

from nti.assessment.interfaces import IQuestionSubmission
from nti.assessment.interfaces import IQAssignmentSubmission
from nti.assessment.interfaces import IQuestionSetSubmission

from nti.assessment.submission import QuestionSubmission
from nti.assessment.submission import AssignmentSubmission
from nti.assessment.submission import QuestionSetSubmission

from nti.externalization.externalization import toExternalObject

from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

from nti.assessment.tests import AssessmentTestCase

from nti.externalization.tests import externalizes


class TestQuestionSubmission(AssessmentTestCase):

    def test_externalizes(self):
        assert_that(QuestionSubmission(),
                    verifiably_provides(IQuestionSubmission))
        assert_that(QuestionSubmission(),
                    externalizes(has_entry('Class', 'QuestionSubmission')))
        assert_that(find_factory_for(toExternalObject(QuestionSubmission())),
                    has_property('_callable', is_(same_instance(QuestionSubmission))))

        # Now verify the same for the mimetype-only version
        assert_that(QuestionSubmission(),
                    externalizes(has_key('MimeType')))
        ext_obj_no_class = toExternalObject(QuestionSubmission())
        ext_obj_no_class.pop('Class')

        assert_that(find_factory_for(ext_obj_no_class),
                    is_(not_none()))

        # No coersion of parts happens yet at this level
        submiss = QuestionSubmission()
        with assert_raises(RequiredMissing):
            update_from_external_object(submiss, {"parts": [u"The text response"]},
                                        require_updater=True)

        update_from_external_object(submiss,
                                    {'questionId': u'foo',
                                     "parts": [u"The text response"],
                                     "version": u'version1999'},
                                    require_updater=True)
        assert_that(submiss,
                    has_property("parts", contains("The text response")))
        assert_that(submiss, has_property("version", is_('version1999')))
        assert_that(has_submitted_file(submiss), is_(False))

    def test_sequence(self):
        submiss = QuestionSubmission()
        update_from_external_object(submiss,
                                    {'questionId': u'foo', 
                                     "parts": [u"The text response"]},
                                    require_updater=True)
        # length
        assert_that(submiss, has_length(1))
        # get
        value = submiss[0]
        assert_that(value, is_(not_none()))
        # set
        submiss[0] = value
        assert_that(submiss[0], is_(value))
        assert_that(submiss, has_length(1))
        # del
        del submiss[0]
        assert_that(submiss, has_length(0))


class TestQuestionSetSubmission(AssessmentTestCase):

    def test_externalizes(self):
        assert_that(QuestionSetSubmission(),
                    verifiably_provides(IQuestionSetSubmission))
        assert_that(QuestionSetSubmission(),
                    externalizes(has_entry('Class', 'QuestionSetSubmission')))

        qss = QuestionSetSubmission()
        with assert_raises(RequiredMissing):
            update_from_external_object(qss, {}, require_updater=True)

        # Wrong type for objects in questions
        with assert_raises(WrongContainedType):
            update_from_external_object(qss, {'questionSetId': u'foo',
                                              "questions": [u"The text response"]},
                                        require_updater=True)

        # Validation is recursive
        with assert_raises(WrongContainedType) as wct:
            update_from_external_object(qss, {'questionSetId': u'foo',
                                              "questions": [QuestionSubmission()]},
                                        require_updater=True)

        assert_that(wct.exception.args[0][0], is_(WrongContainedType))

        update_from_external_object(qss, 
                                    {'questionSetId': u'foo',
                                      "questions": [QuestionSubmission(questionId=u'foo-q', parts=[])]},
                                    require_updater=True)

        assert_that(qss, 
                    has_property('questions', contains(is_(QuestionSubmission))))
        assert_that(has_submitted_file(qss), is_(False))

    def test_mapping(self):
        qss = QuestionSetSubmission()
        update_from_external_object(qss, 
                                    {'questionSetId': u'foo-set',
                                     "questions": [QuestionSubmission(questionId=u'foo-q', parts=[])]},
                                    require_updater=True)

        assert_that(qss, has_length(1))
        assert_that(qss['foo-q'], is_(not_none()))

        qss['foo-q2'] = QuestionSubmission(questionId=u'foo-q2', parts=[])
        assert_that(qss, has_length(2))
        assert_that(qss['foo-q2'], is_(not_none()))

        del qss['foo-q']
        assert_that(qss, has_length(1))
        assert_that(qss.index('foo-q'), is_(-1))


class TestAssignmentSubmission(AssessmentTestCase):

    def test_externalizes(self):
        assert_that(AssignmentSubmission(),
                    verifiably_provides(IQAssignmentSubmission))
        assert_that(AssignmentSubmission(),
                    externalizes(has_entries('Class', 'AssignmentSubmission',
                                             'MimeType', 'application/vnd.nextthought.assessment.assignmentsubmission')))

        asub = AssignmentSubmission()
        assert_that(asub, has_property('lastModified', greater_than(0)))
        assert_that(asub, has_property('createdTime', greater_than(0)))
        # Recursive validation
        with assert_raises(WrongContainedType) as wct:
            update_from_external_object(asub,
                                        {'parts': [QuestionSetSubmission()]},
                                        require_updater=True)
        assert_that(wct.exception.args[0][0][0][0], is_(RequiredMissing))

        update_from_external_object(asub,
                                    {'parts': [QuestionSetSubmission(questionSetId=u'foo', questions=())],
                                     'assignmentId': u'baz'},
                                    require_updater=True)

        assert_that(asub,
                    has_property('parts', contains(is_(QuestionSetSubmission))))

        assert_that(asub, validly_provides(IQAssignmentSubmission))
        assert_that(has_submitted_file(asub), is_(False))

        # time_length
        update_from_external_object(asub,
                                    {'parts': [QuestionSetSubmission(questionSetId=u'foo',
                                                                     questions=(),
                                                                     CreatorRecordedEffortDuration=10)],
                                     'assignmentId': u'baz'},
                                    require_updater=True)

        assert_that(asub, validly_provides(IQAssignmentSubmission))
        assert_that(asub.parts[0],
                    has_property('CreatorRecordedEffortDuration', 10))

        update_from_external_object(asub,
                                    {'parts': [QuestionSetSubmission(questionSetId=u'foo', questions=())],
                                     'assignmentId': u'baz',
                                     'CreatorRecordedEffortDuration': 12},
                                    require_updater=True)

        assert_that(asub, validly_provides(IQAssignmentSubmission))

        assert_that(asub, has_property('CreatorRecordedEffortDuration', 12))

    def test_mapping(self):
        asub = AssignmentSubmission()
        update_from_external_object(asub,
                                    {'parts': [QuestionSetSubmission(questionSetId=u'foo-qs', questions=())],
                                     'assignmentId': u'baz'},
                                    require_updater=True)

        assert_that(asub, has_length(1))
        assert_that(asub['foo-qs'], is_(not_none()))

        asub['foo-qs2'] = QuestionSetSubmission(questionSetId=u'foo-qs2', 
                                                questions=())
        assert_that(asub, has_length(2))
        assert_that(asub['foo-qs2'], is_(not_none()))

        del asub['foo-qs']
        assert_that(asub, has_length(1))
        assert_that(asub.index('foo-qs'), is_(-1))
