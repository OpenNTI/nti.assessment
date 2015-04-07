#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
from hamcrest.core.core.isinstanceof import instance_of
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import contains
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import greater_than
from hamcrest import has_property

from zope import component
from zope.schema.interfaces import WrongContainedType

from nti.externalization.externalization import toExternalObject
from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

from nti.assessment.interfaces import IQPoll
from nti.assessment.interfaces import IQSurvey
from nti.assessment.interfaces import IQPollSubmission
from nti.assessment.interfaces import IQSurveySubmission
from nti.assessment.interfaces import IQNonGradableMultipleChoicePart

from nti.assessment.interfaces import IQAggregatedMultipleChoicePart

from nti.assessment.parts import QNonGradableFreeResponsePart
from nti.assessment.parts import QNonGradableMultipleChoicePart

from nti.assessment.survey import QPoll
from nti.assessment.survey import QSurvey
from nti.assessment.survey import QPollSubmission
from nti.assessment.survey import QSurveySubmission

from nti.assessment.interfaces import IQAggregatedPoll
from nti.assessment.survey import QAggregatedMultipleChoicePart

from nti.externalization.tests import externalizes

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

from nose.tools import assert_raises

from nti.assessment.tests import AssessmentTestCase

class TestSurvey(AssessmentTestCase):

	def test_part_provides(self):
		assert_that( QNonGradableMultipleChoicePart(), 
					 verifiably_provides(IQNonGradableMultipleChoicePart ) )

		assert_that( QNonGradableMultipleChoicePart(),
					 externalizes( has_entries( 'Class', 'MultipleChoicePart',
												'MimeType', 'application/vnd.nextthought.assessment.nongradablemultiplechoicepart' ) ) )

		part = QNonGradableMultipleChoicePart( choices=list(("A", "B", "C")) )
		assert_that( part, verifiably_provides( IQNonGradableMultipleChoicePart ) )
		assert_that( part, is_( part ) )
		assert_that( hash(part), is_( hash(part) ) )

	def test_internalize(self):
		part = QNonGradableMultipleChoicePart(choices=[u''], content=u'here')
		poll = QPoll( parts=(part,) )
		ext_obj= toExternalObject( poll )
		factory = find_factory_for(ext_obj)
		obj = factory()
		update_from_external_object(obj, ext_obj, notify=False)
		assert_that(obj.parts[0], instance_of(QNonGradableMultipleChoicePart))
		
	def test_externalizes(self):
		part = QNonGradableFreeResponsePart()
		poll = QPoll( parts=(part,) )
		
		assert_that( poll, verifiably_provides( IQPoll ) )
		assert_that( find_factory_for( toExternalObject( poll ) ),
					 is_not( none() ) )
		assert_that( poll,
					 externalizes( has_entries( 'Class', 'Poll',
												'MimeType', 'application/vnd.nextthought.napoll' ) ) )
		survey = QSurvey(questions=(poll,))
		assert_that( survey, verifiably_provides( IQSurvey ) )
		assert_that( find_factory_for( toExternalObject( survey ) ),
					 is_not( none() ) )
		assert_that( survey,
					 externalizes( has_entries( 'Class', 'Survey',
												'MimeType', 'application/vnd.nextthought.nasurvey' ) ) )


		assert_that( QPollSubmission(), verifiably_provides( IQPollSubmission ) )
		assert_that( QPollSubmission(), externalizes( has_entries('Class', 'PollSubmission',
																  'MimeType', 'application/vnd.nextthought.assessment.pollsubmission') ) )
		
		assert_that( QSurveySubmission(), verifiably_provides( IQSurveySubmission ) )
		assert_that( QSurveySubmission(), externalizes( has_entries( 'Class', 'SurveySubmission',
																	 'MimeType', 'application/vnd.nextthought.assessment.surveysubmission') ) )

		ssub = QSurveySubmission()
		assert_that( ssub, has_property('lastModified', greater_than(0)))
		assert_that( ssub, has_property('createdTime', greater_than(0)))
		# Recursive validation
		with assert_raises(WrongContainedType):
			update_from_external_object( ssub,
										 {'questions': [QPollSubmission()]},
										 require_updater=True )

		update_from_external_object( ssub,
 									 {'questions': [QPollSubmission(pollId='foo', parts=())],
 									  'surveyId': 'baz'},
 									 require_updater=True )

		assert_that( ssub, has_property( 'questions', contains( is_( QPollSubmission ) ) ) )

		assert_that( ssub, validly_provides( IQSurveySubmission ))

		# time_length
		update_from_external_object( ssub,
									 {'questions': [QPollSubmission(pollId='foo', parts=(),
																	CreatorRecordedEffortDuration=10)],
									  'surveyId': 'baz'},
									 require_updater=True )

		assert_that( ssub, validly_provides( IQSurveySubmission ))
		assert_that( ssub.questions[0], has_property('CreatorRecordedEffortDuration', 10) )

		update_from_external_object( ssub,
									 {'questions': [QPollSubmission(pollId='foo', parts=())],
									  'surveyId': 'baz',
									  'CreatorRecordedEffortDuration': 12},
									 require_updater=True )

		assert_that( ssub, validly_provides( IQSurveySubmission ))
		assert_that( ssub, has_property('CreatorRecordedEffortDuration', 12))
		
	def test_mapping(self):
		ssub = QSurveySubmission()
		update_from_external_object( ssub,
									 {'questions': [QPollSubmission(pollId='foo-ps', parts=())],
									  'surveyId': 'baz'},
									 require_updater=True )
		
		assert_that(ssub, has_length(1))
		assert_that(ssub['foo-ps'], is_not(none()))
		
		ssub['foo-ps2'] = QPollSubmission(pollId='foo-ps2', parts=())
		assert_that(ssub, has_length(2))
		assert_that(ssub['foo-ps2'], is_not(none()))
	
		del ssub['foo-ps']
		assert_that(ssub, has_length(1))
		assert_that(ssub.index('foo-ps'), is_(-1))

class TestAggregation(AssessmentTestCase):
	
	def test_externalizes(self):
		assert_that(QAggregatedMultipleChoicePart(), verifiably_provides(IQAggregatedMultipleChoicePart) )
		assert_that(QAggregatedMultipleChoicePart(), 
					externalizes(has_entries('Class', 'AggregatedMultipleChoicePart',
								 			 'MimeType', 'application/vnd.nextthought.assessment.aggregatedmultiplechoicepart' )) )
		assert_that( find_factory_for( toExternalObject( QAggregatedMultipleChoicePart() ) ),
					 is_( none() ) )

	def test_aggregation_poll(self):
		part = QNonGradableMultipleChoicePart(choices=[u'a', 'b', 'c'], content=u'here')
		poll = QPoll(parts=(part,))
		poll.ntiid = 'tag:nextthought.com,2011-10:AOPS-HTML-poll.0'
		component.globalSiteManager.registerUtility(poll, IQPoll, name=poll.ntiid)
		
		poll_1 = QPollSubmission(pollId=poll.ntiid, parts=(1,))
		aggregated = IQAggregatedPoll(poll_1, None)
		assert_that(aggregated, is_not(none()))
		assert_that(aggregated, has_length(1))
		assert_that(aggregated, has_property('parts', has_length(1)))
		assert_that(aggregated.parts[0], has_property('Results', has_entry(1,1)))
		
		poll_2 = QPollSubmission(pollId=poll.ntiid, parts=(1,))
		aggregated_2 = IQAggregatedPoll(poll_2, None)
		
		aggregated += aggregated_2
		assert_that(aggregated.parts[0], has_property('Results', has_entry(1,2)))
