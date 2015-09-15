#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
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
from hamcrest import instance_of
from hamcrest import greater_than
from hamcrest import has_property

from zope import component

from zope.schema.interfaces import WrongContainedType

from nti.assessment.interfaces import IQPoll
from nti.assessment.interfaces import IQSurvey
from nti.assessment.interfaces import IQPollSubmission
from nti.assessment.interfaces import IQSurveySubmission
from nti.assessment.interfaces import IQNonGradableMultipleChoicePart

from nti.assessment.interfaces import IQAggregatedMultipleChoicePart
from nti.assessment.interfaces import IQAggregatedMultipleChoiceMultipleAnswerPart

from nti.assessment.parts import QNonGradableFreeResponsePart
from nti.assessment.parts import QNonGradableMultipleChoicePart

from nti.assessment.survey import QPoll
from nti.assessment.survey import QSurvey
from nti.assessment.survey import QPollSubmission
from nti.assessment.survey import QSurveySubmission

from nti.assessment.interfaces import IQAggregatedPoll
from nti.assessment.survey import QAggregatedMultipleChoicePart
from nti.assessment.survey import QAggregatedMultipleChoiceMultipleAnswerPart

from nti.assessment.response import QModeledContentResponse

from nti.externalization.externalization import toExternalObject
from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

from nti.externalization.tests import externalizes

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

from nose.tools import assert_raises

from nti.assessment.tests import AssessmentTestCase

class TestSurvey(AssessmentTestCase):

	def test_part_provides(self):
		assert_that(QNonGradableMultipleChoicePart(),
					 verifiably_provides(IQNonGradableMultipleChoicePart))

		assert_that(QNonGradableMultipleChoicePart(),
					 externalizes(has_entries('Class', 'MultipleChoicePart',
											  'MimeType', 'application/vnd.nextthought.assessment.nongradablemultiplechoicepart')))

		part = QNonGradableMultipleChoicePart(choices=list(("A", "B", "C")))
		assert_that(part, verifiably_provides(IQNonGradableMultipleChoicePart))
		assert_that(part, is_(part))
		assert_that(hash(part), is_(hash(part)))

	def test_internalize(self):
		part = QNonGradableMultipleChoicePart(choices=[u''], content=u'here')
		poll = QPoll(parts=(part,), content=u'foo')
		ext_obj = toExternalObject(poll)
		factory = find_factory_for(ext_obj)
		obj = factory()
		update_from_external_object(obj, ext_obj, notify=False)
		assert_that(obj, has_property('content', is_(u'foo')))
		assert_that(obj.parts[0], instance_of(QNonGradableMultipleChoicePart))

	def test_externalizes(self):
		part = QNonGradableFreeResponsePart()
		poll = QPoll(parts=(part,))

		assert_that(poll, verifiably_provides(IQPoll))
		assert_that(find_factory_for(toExternalObject(poll)),
					 is_not(none()))
		assert_that(poll,
					 externalizes(has_entries('Class', 'Poll',
											  'MimeType', 'application/vnd.nextthought.napoll')))
		survey = QSurvey(questions=(poll,))
		assert_that(survey, verifiably_provides(IQSurvey))
		assert_that(find_factory_for(toExternalObject(survey)),
					 is_not(none()))
		assert_that(survey,
					 externalizes(has_entries('Class', 'Survey',
											  'MimeType', 'application/vnd.nextthought.nasurvey')))


		assert_that(QPollSubmission(), verifiably_provides(IQPollSubmission))
		assert_that(QPollSubmission(), externalizes(has_entries('Class', 'PollSubmission',
																'MimeType', 'application/vnd.nextthought.assessment.pollsubmission')))

		assert_that(QSurveySubmission(), verifiably_provides(IQSurveySubmission))
		assert_that(QSurveySubmission(), externalizes(has_entries('Class', 'SurveySubmission',
																  'MimeType', 'application/vnd.nextthought.assessment.surveysubmission')))

		ssub = QSurveySubmission()
		assert_that(ssub, has_property('lastModified', greater_than(0)))
		assert_that(ssub, has_property('createdTime', greater_than(0)))
		# Recursive validation
		with assert_raises(WrongContainedType):
			update_from_external_object(ssub,
										{'questions': [QPollSubmission()]},
										  require_updater=True)

		update_from_external_object(ssub,
 									 {'questions': [QPollSubmission(pollId='foo', parts=())],
 									  'surveyId': 'baz'},
 									 require_updater=True)

		assert_that(ssub, has_property('questions', contains(is_(QPollSubmission))))

		assert_that(ssub, validly_provides(IQSurveySubmission))

		# time_length
		update_from_external_object(ssub,
									 {'questions': [QPollSubmission(pollId='foo', parts=(),
																	CreatorRecordedEffortDuration=10)],
									  'surveyId': 'baz'},
									 require_updater=True)

		assert_that(ssub, validly_provides(IQSurveySubmission))
		assert_that(ssub.questions[0], has_property('CreatorRecordedEffortDuration', 10))

		update_from_external_object(ssub,
									 {'questions': [QPollSubmission(pollId='foo', parts=())],
									  'surveyId': 'baz',
									  'CreatorRecordedEffortDuration': 12},
									 require_updater=True)

		assert_that(ssub, validly_provides(IQSurveySubmission))
		assert_that(ssub, has_property('CreatorRecordedEffortDuration', 12))

	def test_mapping(self):
		ssub = QSurveySubmission()
		update_from_external_object(ssub,
									 {'questions': [QPollSubmission(pollId='foo-ps', parts=())],
									  'surveyId': 'baz'},
									 require_updater=True)

		assert_that(ssub, has_length(1))
		assert_that(ssub['foo-ps'], is_not(none()))

		ssub['foo-ps2'] = QPollSubmission(pollId='foo-ps2', parts=())
		assert_that(ssub, has_length(2))
		assert_that(ssub['foo-ps2'], is_not(none()))

		del ssub['foo-ps']
		assert_that(ssub, has_length(1))
		assert_that(ssub.index('foo-ps'), is_(-1))
		
	def test_parsing(self):
		external = \
		{u'CreatorRecordedEffortDuration': 329870,
 		 u'MimeType': u'application/vnd.nextthought.assessment.surveysubmission',
 		 u'parts': [],
 		 u'questions': [{u'CreatorRecordedEffortDuration': None,
                 u'MimeType': u'application/vnd.nextthought.assessment.pollsubmission',
                 u'NTIID': u'tag:nextthought.com,2011-10:NTIAlpha-NAQ-NTI1000_TestCourse.naq.qid.poll_test.01',
                 u'parts': [{u'0': 2, u'1': 0, u'2': 1, u'3': 3}],
                 u'pollId': u'tag:nextthought.com,2011-10:NTIAlpha-NAQ-NTI1000_TestCourse.naq.qid.poll_test.01'},
                {u'CreatorRecordedEffortDuration': None,
                 u'MimeType': u'application/vnd.nextthought.assessment.pollsubmission',
                 u'NTIID': u'tag:nextthought.com,2011-10:NTIAlpha-NAQ-NTI1000_TestCourse.naq.qid.poll_test.02',
                 u'parts': [{u'0': 1, u'1': 0, u'2': 2, u'3': 3}],
                 u'pollId': u'tag:nextthought.com,2011-10:NTIAlpha-NAQ-NTI1000_TestCourse.naq.qid.poll_test.02'},
                {u'CreatorRecordedEffortDuration': None,
                 u'MimeType': u'application/vnd.nextthought.assessment.pollsubmission',
                 u'NTIID': u'tag:nextthought.com,2011-10:NTIAlpha-NAQ-NTI1000_TestCourse.naq.qid.poll_test.03',
                 u'parts': [0],
                 u'pollId': u'tag:nextthought.com,2011-10:NTIAlpha-NAQ-NTI1000_TestCourse.naq.qid.poll_test.03'},
                {u'CreatorRecordedEffortDuration': None,
                 u'MimeType': u'application/vnd.nextthought.assessment.pollsubmission',
                 u'NTIID': u'tag:nextthought.com,2011-10:NTIAlpha-NAQ-NTI1000_TestCourse.naq.qid.poll_test.04',
                 u'parts': [{u'MimeType': u'application/vnd.nextthought.assessment.modeledcontentresponse',
                             u'value': [u'\u200bCoco']}],
                 u'pollId': u'tag:nextthought.com,2011-10:NTIAlpha-NAQ-NTI1000_TestCourse.naq.qid.poll_test.04'}],
		 u'surveyId': u'tag:nextthought.com,2011-10:NTIAlpha-NAQ-NTI1000_TestCourse.naq.survey.survey_test'}

		factory = find_factory_for(external)
		assert_that(factory, is_not(none()))
		submission = factory()
		update_from_external_object(submission, external,  require_updater=True)
		assert_that(submission, has_length(4))
		
		psub = submission.get('tag:nextthought.com,2011-10:NTIAlpha-NAQ-NTI1000_TestCourse.naq.qid.poll_test.04')
		assert_that(psub, is_not(none()))
		assert_that(psub, has_length(1))
		assert_that(psub[0], is_(QModeledContentResponse))
		assert_that(psub[0], has_property('value', is_((u'\u200bCoco',))))

class TestAggregation(AssessmentTestCase):

	def test_externalizes(self):
		assert_that(QAggregatedMultipleChoicePart(), verifiably_provides(IQAggregatedMultipleChoicePart))
		assert_that(QAggregatedMultipleChoicePart(),
					externalizes(has_entries('Class', 'AggregatedMultipleChoicePart',
								 			 'MimeType', 'application/vnd.nextthought.assessment.aggregatedmultiplechoicepart')))
		assert_that(find_factory_for(toExternalObject(QAggregatedMultipleChoicePart())),
					is_(none()))
		
		assert_that(QAggregatedMultipleChoiceMultipleAnswerPart(), verifiably_provides(IQAggregatedMultipleChoiceMultipleAnswerPart))
		assert_that(QAggregatedMultipleChoiceMultipleAnswerPart(),
					externalizes(has_entries('Class', 'AggregatedMultipleChoiceMultipleAnswerPart',
								 			 'MimeType', 'application/vnd.nextthought.assessment.aggregatedmultiplechoicemultipleanswerpart')))
		assert_that(find_factory_for(toExternalObject(QAggregatedMultipleChoiceMultipleAnswerPart())),
					is_(none()))

	def test_multiple_choice_multple_answer(self):
		p = QAggregatedMultipleChoiceMultipleAnswerPart()
		p.append((2,3,5))
		ext_obj = toExternalObject(p)
		assert_that(ext_obj, has_entry('Results', has_entry('(2, 3, 5)', 1)))
		
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
		assert_that(aggregated.parts[0], has_property('Results', has_entry(1, 1)))

		poll_2 = QPollSubmission(pollId=poll.ntiid, parts=(1,))
		aggregated_2 = IQAggregatedPoll(poll_2, None)

		aggregated += aggregated_2
		assert_that(aggregated.parts[0], has_property('Results', has_entry(1, 2)))
