#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_key
from hamcrest import not_none
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import has_entries
from hamcrest import assert_that
from hamcrest import contains_inanyorder

import unittest

from nti.assessment import FIELDS
from nti.assessment import ACCEPTS

from nti.assessment.assignment import QAssignment
from nti.assessment.assignment import QAssignmentPart

from nti.assessment.interfaces import QUESTION_MIME_TYPE
from nti.assessment.interfaces import QUESTION_SET_MIME_TYPE

from nti.assessment.parts import QMatchingPart

from nti.assessment.question import QQuestion
from nti.assessment.question import QQuestionSet

from nti.assessment.tests import SharedConfiguringTestLayer


class TestJsonSchema(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_assignment_part(self):
        a = QAssignmentPart()
        schema = a.schema()
        assert_that(schema, has_key(FIELDS))
        fields = schema[FIELDS]
        assert_that(fields, has_length(4))
        assert_that(fields, has_entry('content', has_entry('type', 'string')))
        assert_that(fields, 
					has_entry('title', has_entry('min_length', is_(0))))

        assert_that(fields, 
					has_entry('question_set', has_entry('type', not_none())))
        assert_that(fields, has_entry('auto_grade', has_entry('type', 'bool')))

        assert_that(schema, has_key(ACCEPTS))
        accepts = schema[ACCEPTS]
        assert_that(accepts, has_length(1))
        assert_that(accepts, has_key(QUESTION_SET_MIME_TYPE))

    def test_question(self):
        a = QQuestion()
        schema = a.schema()
        assert_that(schema, has_key(FIELDS))
        fields = schema[FIELDS]
        assert_that(fields, has_length(5))
        assert_that(fields, has_entry('content', has_entry('type', 'string')))
        assert_that(fields, has_entry('parts', has_entry('type', 'List')))
        assert_that(fields, has_entry('tags', has_entry('type', 'List')))
        assert_that(fields, 
					has_entry('tags', has_entry('base_type', 'string')))

        assert_that(schema, has_key(ACCEPTS))
        accepts = schema[ACCEPTS]
        assert_that(accepts, has_length(8))
        assert_that(accepts, 
					contains_inanyorder(
			            'application/vnd.nextthought.assessment.matchingpart',
			            'application/vnd.nextthought.assessment.filepart',
			            'application/vnd.nextthought.assessment.multiplechoicemultipleanswerpart',
			            'application/vnd.nextthought.assessment.orderingpart',
			            'application/vnd.nextthought.assessment.multiplechoicepart',
			            'application/vnd.nextthought.assessment.modeledcontentpart',
			            'application/vnd.nextthought.assessment.connectingpart',
			            'application/vnd.nextthought.assessment.freeresponsepart'))

    def test_qpart(self):
        a = QMatchingPart()
        schema = a.schema()
        assert_that(schema, has_key(FIELDS))
        fields = schema[FIELDS]
        assert_that(fields, has_length(8))
        assert_that(fields, has_entry('explanation',
                                      has_entry('base_type', 'string')))
        assert_that(fields, has_entry('weight', has_entry('type', 'Number')))
        assert_that(fields, 
					has_entry('weight', has_entry('base_type', 'float')))
        assert_that(fields, has_entry('labels', has_entry('type', 'list')))
        assert_that(fields, 
					has_entry('content', has_entry('base_type', 'string')))
        assert_that(fields, has_entry('solutions', has_entry('type', 'List')))
        assert_that(fields, has_entry('hints', has_entry('type', 'List')))

    def test_qset(self):
        a = QQuestionSet()
        schema = a.schema()
        assert_that(schema, has_key(FIELDS))
        fields = schema[FIELDS]
        assert_that(fields, has_length(4))
        assert_that(fields, 
					has_entry('title', has_entry('min_length', is_(0))))
        assert_that(fields, has_entry('questions', has_entry('type', 'List')))

        assert_that(schema, has_key(ACCEPTS))
        accepts = schema[ACCEPTS]
        assert_that(accepts, has_length(1))
        assert_that(accepts, has_key(QUESTION_MIME_TYPE))
        assert_that(accepts.get(QUESTION_MIME_TYPE).get(ACCEPTS), 
				    has_length(8))

    def test_assignment(self):
        a = QAssignment()
        schema = a.schema()
        assert_that(schema, has_key(FIELDS))
        fields = schema[FIELDS]
        assert_that(fields, has_length(14))
        assert_that(fields, has_entry('parts', 
									  has_entry('base_type',
                                                'application/vnd.nextthought.assessment.assignmentpart')))
        assert_that(fields, 
					has_entry('title', has_entry('min_length', is_(1))))
        assert_that(fields, 
					has_entry('is_non_public', has_entry('type', 'bool')))
        assert_that(fields, has_entry('available_for_submission_beginning',
                                      has_entry('type', 'datetime')))
        assert_that(fields, has_entry('version',
                                      has_entries('type', 'string',
                                                  'readonly', True,
                                                  'required', False)))

        assert_that(schema, has_key(ACCEPTS))
        accepts = schema[ACCEPTS]
        assert_that(accepts, has_length(1))
        assert_that(accepts, 
					has_key('application/vnd.nextthought.assessment.assignmentpart'))
