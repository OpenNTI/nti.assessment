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

from nti.coremetadata.interfaces import ILastModified

from nti.externalization.externalization import toExternalObject
from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

from nti.assessment.interfaces import IQPoll
from nti.assessment.interfaces import IQSurvey
from nti.assessment.interfaces import IQSubmittedPoll
from nti.assessment.interfaces import IQSubmittedSurvey
from nti.assessment.interfaces import IQNonGradableMultipleChoicePart

from nti.assessment.common import QSubmittedPart

from nti.assessment.parts import QNonGradableFreeResponsePart
from nti.assessment.parts import QNonGradableMultipleChoicePart

from nti.assessment.poll import QPoll
from nti.assessment.poll import QSurvey
from nti.assessment.poll import QSubmittedPoll
from nti.assessment.poll import QPollSubmission
from nti.assessment.poll import QSubmittedSurvey
from nti.assessment.poll import QSurveySubmission

from nti.externalization.tests import externalizes

from nti.testing.matchers import verifiably_provides

from nti.assessment.tests import lineage
from nti.assessment.tests import AssessmentTestCase
from nti.assessment.tests import check_old_dublin_core

class TestPoll(AssessmentTestCase):

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

		assert_that( QSubmittedPoll(), verifiably_provides( IQSubmittedPoll ) )
		assert_that( QSubmittedPoll(), verifiably_provides( ILastModified ) )
		assert_that( QSubmittedPoll(), externalizes( has_entries( 'Class', 'SubmittedPoll',
																  'MimeType', 'application/vnd.nextthought.assessment.submittedpoll') ) )
		assert_that( find_factory_for( toExternalObject ( QSubmittedPoll() ) ),
					 is_( none() ) )
		
		assert_that( QSubmittedSurvey(), verifiably_provides( IQSubmittedSurvey ) )
		assert_that( QSubmittedSurvey(), verifiably_provides( ILastModified ) )
		assert_that( QSubmittedSurvey(), externalizes( has_entries( 'Class', 'SubmittedSurvey',
																	'MimeType', 'application/vnd.nextthought.assessment.submittedsurvey') ) )
		assert_that( find_factory_for( toExternalObject(QSubmittedSurvey() ) ),
					 is_( none() ) )

	def test_submitted_poll(self):
		part = QNonGradableFreeResponsePart()
		poll = QPoll( parts=(part,) )
		component.provideUtility( poll, provides=IQPoll,  name="1")

		sub = QPollSubmission( )
		update_from_external_object( sub, {'pollId':"1", 'parts': ['correct']},
									 notify=False)

		assert_that( sub, has_property( 'pollId', "1" ) )
		assert_that( sub, has_property( 'parts', is_(['correct'])) )

		result = IQSubmittedPoll( sub )
		assert_that( result, has_property( 'pollId', "1" ) )
		assert_that( result, has_property( 'parts', contains( QSubmittedPart( submittedResponse='correct') ) ) )
		
		check_old_dublin_core(result)
		
	def test_submitted_poll_non_part(self):
		part = QNonGradableFreeResponsePart()
		poll = QPoll( parts=(part,) )
		component.provideUtility( poll, provides=IQPoll,  name="1")

		sub = QPollSubmission( )
		update_from_external_object( sub, {'pollId':"1", 'parts': [None]},
									 notify=False)

		result = IQSubmittedPoll( sub )
		assert_that( result, has_property( 'pollId', "1" ) )
		assert_that( result, has_property( 'parts', contains( QSubmittedPart( submittedResponse=None) ) ) )

	def test_submitted_survey(self):
		part = QNonGradableFreeResponsePart()
		poll = QPoll( parts=(part,) )
		survey = QSurvey( questions=(poll,) )

		component.provideUtility( poll,
								  provides=IQPoll,
								  name="1" )
		component.provideUtility( survey,
								  provides=IQSurvey,
								  name="2" )

		sub = QPollSubmission( pollId="1", parts=('correct',) )
		set_sub = QSurveySubmission( surveyId="2", questions=(sub,) )

		result = IQSubmittedSurvey( set_sub )

		assert_that( result, has_property( 'surveyId', "2" ) )
		assert_that( result, has_property( 'questions',
										   contains( has_property( 'parts',
																  contains( QSubmittedPart( submittedResponse='correct' ) ) ) ) ) )
		# consistent hashing
		assert_that( hash(result), is_(hash(result)))
		
		for question in result.questions:
			parents = list(lineage(question))
			assert_that(parents, has_length(1))
					
		ext_obj = toExternalObject( result ) # set lineage
		assert_that( ext_obj, has_entry( 'questions', has_length( 1 ) ) )

		check_old_dublin_core(result)
				
		for poll in result.polls:
			parents = list(lineage(poll))
			assert_that(parents[-1], is_(result))
			assert_that(parents, has_length(greater_than(1)))
			for part in poll.parts:
				parents = list(lineage(part))
				assert_that(parents, has_length(greater_than(2)))
				assert_that(parents[-1], is_(result))
