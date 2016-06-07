#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
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

from zope.schema.interfaces import RequiredMissing
from zope.schema.interfaces import WrongContainedType

from nti.externalization.externalization import toExternalObject

from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

from nti.assessment import interfaces
from nti.assessment import submission

from nose.tools import assert_raises

from nti.externalization.tests import externalizes

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

from nti.assessment.tests import AssessmentTestCase

class TestQuestionSubmission(AssessmentTestCase):

	def test_externalizes(self):
		assert_that( submission.QuestionSubmission(), verifiably_provides( interfaces.IQuestionSubmission ) )
		assert_that( submission.QuestionSubmission(), externalizes( has_entry( 'Class', 'QuestionSubmission' ) ) )
		assert_that( find_factory_for( toExternalObject( submission.QuestionSubmission() ) ),
					 has_property( '_callable', is_( same_instance( submission.QuestionSubmission ) ) ) )


		# Now verify the same for the mimetype-only version
		assert_that( submission.QuestionSubmission(), externalizes( has_key( 'MimeType' ) ) )
		ext_obj_no_class = toExternalObject( submission.QuestionSubmission() )
		ext_obj_no_class.pop( 'Class' )

		assert_that( find_factory_for( ext_obj_no_class ),
					 is_( not_none() ) )

		# No coersion of parts happens yet at this level
		submiss = submission.QuestionSubmission()
		with assert_raises(RequiredMissing):
			update_from_external_object(submiss, {"parts": ["The text response"]},
										require_updater=True )

		update_from_external_object(submiss,
									{'questionId': 'foo',
									 "parts": ["The text response"],
									 "version": 'version1999'},
									require_updater=True )
		assert_that( submiss, has_property( "parts", contains( "The text response" ) ) )
		assert_that( submiss, has_property( "version", is_('version1999') ))

	def test_sequence(self):
		submiss = submission.QuestionSubmission()
		update_from_external_object(submiss, {'questionId': 'foo', "parts": ["The text response"]},
									require_updater=True )
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
		assert_that( submission.QuestionSetSubmission(), verifiably_provides( interfaces.IQuestionSetSubmission ) )
		assert_that( submission.QuestionSetSubmission(), externalizes( has_entry( 'Class', 'QuestionSetSubmission' ) ) )

		qss = submission.QuestionSetSubmission()
		with assert_raises(RequiredMissing):
			update_from_external_object( qss, {}, require_updater=True )

		# Wrong type for objects in questions
		with assert_raises(WrongContainedType):
			update_from_external_object( qss, {'questionSetId': 'foo',
											   "questions": ["The text response"]}, require_updater=True )

		# Validation is recursive
		with assert_raises(WrongContainedType) as wct:
			update_from_external_object( qss, {'questionSetId': 'foo',
											   "questions": [submission.QuestionSubmission()]}, require_updater=True )

		assert_that( wct.exception.args[0][0], is_(WrongContainedType ) )

		update_from_external_object( qss, {'questionSetId': 'foo',
										   "questions": [submission.QuestionSubmission(questionId='foo', parts=[])]},
									require_updater=True )

		assert_that( qss, has_property( 'questions', contains( is_( submission.QuestionSubmission ) ) ) )

	def test_mapping(self):
		qss = submission.QuestionSetSubmission()
		update_from_external_object(qss, {'questionSetId': 'foo-set',
										  "questions": [submission.QuestionSubmission(questionId='foo-q', parts=[])]},
									require_updater=True )

		assert_that(qss, has_length(1))
		assert_that(qss['foo-q'], is_(not_none()))

		qss['foo-q2'] = submission.QuestionSubmission(questionId='foo-q2', parts=[])
		assert_that(qss, has_length(2))
		assert_that(qss['foo-q2'], is_(not_none()))

		del qss['foo-q']
		assert_that(qss, has_length(1))
		assert_that(qss.index('foo-q'), is_(-1))

class TestAssignmentSubmission(AssessmentTestCase):

	def test_externalizes(self):
		assert_that( submission.AssignmentSubmission(), verifiably_provides( interfaces.IQAssignmentSubmission ) )
		assert_that( submission.AssignmentSubmission(), externalizes( has_entries( 'Class', 'AssignmentSubmission',
																				   'MimeType', 'application/vnd.nextthought.assessment.assignmentsubmission') ) )

		asub = submission.AssignmentSubmission()
		assert_that( asub, has_property('lastModified', greater_than(0)))
		assert_that( asub, has_property('createdTime', greater_than(0)))
		# Recursive validation
		with assert_raises(WrongContainedType) as wct:
			update_from_external_object( asub,
										 {'parts': [submission.QuestionSetSubmission()]},
										 require_updater=True )
		assert_that( wct.exception.args[0][0][0][0][1], is_(RequiredMissing ) )


		update_from_external_object( asub,
									 {'parts': [submission.QuestionSetSubmission(questionSetId='foo', questions=())],
									  'assignmentId': 'baz'},
									 require_updater=True )

		assert_that( asub, has_property( 'parts', contains( is_( submission.QuestionSetSubmission ) ) ) )

		assert_that( asub, validly_provides( interfaces.IQAssignmentSubmission ))

		# time_length
		update_from_external_object( asub,
									 {'parts': [submission.QuestionSetSubmission(questionSetId='foo',
																				 questions=(),
																				 CreatorRecordedEffortDuration=10)],
									  'assignmentId': 'baz'},
									 require_updater=True )

		assert_that( asub, validly_provides( interfaces.IQAssignmentSubmission ))
		assert_that( asub.parts[0], has_property('CreatorRecordedEffortDuration', 10) )

		update_from_external_object( asub,
									 {'parts': [submission.QuestionSetSubmission(questionSetId='foo', questions=())],
									  'assignmentId': 'baz',
									  'CreatorRecordedEffortDuration': 12},
									 require_updater=True )

		assert_that( asub, validly_provides( interfaces.IQAssignmentSubmission ))

		assert_that( asub, has_property('CreatorRecordedEffortDuration', 12))

	def test_mapping(self):
		asub = submission.AssignmentSubmission()
		update_from_external_object( asub,
									 {'parts': [submission.QuestionSetSubmission(questionSetId='foo-qs', questions=())],
									  'assignmentId': 'baz'},
									 require_updater=True )

		assert_that(asub, has_length(1))
		assert_that(asub['foo-qs'], is_(not_none()))

		asub['foo-qs2'] = submission.QuestionSetSubmission(questionSetId='foo-qs2', questions=())
		assert_that(asub, has_length(2))
		assert_that(asub['foo-qs2'], is_(not_none()))

		del asub['foo-qs']
		assert_that(asub, has_length(1))
		assert_that(asub.index('foo-qs'), is_(-1))
