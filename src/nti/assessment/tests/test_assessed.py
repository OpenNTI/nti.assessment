#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import assert_that
from hamcrest import has_entry
from hamcrest import has_entries
from hamcrest import is_
from hamcrest import has_property
from hamcrest import contains
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import greater_than
from hamcrest import calling
from hamcrest import raises

import time
import datetime

from zope import interface
from zope import component

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.dublincore.annotatableadapter import ZDCAnnotatableAdapter

from nti.coremetadata.interfaces import ILastModified

from nti.externalization import internalization
from nti.externalization.externalization import toExternalObject
from nti.externalization.internalization import update_from_external_object

from nti.schema.field import InvalidValue

from nti.assessment import parts
from nti.assessment import assessed
from nti.assessment import response
from nti.assessment import submission
from nti.assessment import interfaces
from nti.assessment import solution as solutions
from nti.assessment.question import QQuestion, QQuestionSet

from nti.externalization.tests import externalizes

from nti.testing.matchers import is_false
from nti.testing.matchers import verifiably_provides

from nti.assessment.tests import AssessmentTestCase

def _check_old_dublin_core( qaq ):
	"we can read old dublin core metadata"

	del qaq.__dict__['lastModified']
	del qaq.__dict__['createdTime']

	assert_that( qaq.lastModified, is_( 0 ) )
	assert_that( qaq.createdTime, is_( 0 ) )


	interface.alsoProvides( qaq, IAttributeAnnotatable )

	zdc = ZDCAnnotatableAdapter( qaq )

	now = datetime.datetime.now()

	zdc.created = now
	zdc.modified = now

	assert_that( qaq.lastModified, is_( time.mktime( now.timetuple() ) ) )
	assert_that( qaq.createdTime, is_( time.mktime( now.timetuple() ) ) )

def lineage(resource):
	while resource is not None:
		yield resource
		try:
			resource = resource.__parent__
		except AttributeError:
			resource = None

class TestAssessedPart(AssessmentTestCase):

	def test_externalizes(self):
		assert_that( assessed.QAssessedPart(), verifiably_provides( interfaces.IQAssessedPart ) )
		assert_that( assessed.QAssessedPart(), externalizes( has_entry( 'Class', 'AssessedPart' ) ) )
		assert_that( internalization.find_factory_for( toExternalObject( assessed.QAssessedPart() ) ),
					 is_( none() ) )

		# These cannot be created externally, so we're not worried about
		# what happens when they are updated...this test just serves to document
		# the behaviour. In the past, updating from external objects transformed
		# the value into an IQResponse...but the actual assessment code itself assigned
		# the raw string/int value. Responses would be ideal, but that could break existing
		# client code. The two behaviours are now unified
		part = assessed.QAssessedPart()
		update_from_external_object( part, {"submittedResponse": "The text response"}, require_updater=True )

		assert_that( part.submittedResponse, is_( "The text response" ) )

	def test_hash(self):
		part = assessed.QAssessedPart(submittedResponse=[1,2,3])
		hash(part)
		assert_that(part, is_(part))

class TestAssessedQuestion(AssessmentTestCase):

	def test_externalizes(self):
		assert_that( assessed.QAssessedQuestion(), verifiably_provides( interfaces.IQAssessedQuestion ) )
		assert_that( assessed.QAssessedQuestion(), verifiably_provides( ILastModified ) )
		assert_that( assessed.QAssessedQuestion(), externalizes( has_entry( 'Class', 'AssessedQuestion' ) ) )
		assert_that( internalization.find_factory_for( toExternalObject( assessed.QAssessedQuestion() ) ),
					 is_( none() ) )

	def test_assess(self):
		part = parts.QFreeResponsePart(solutions=(solutions.QFreeResponseSolution(value='correct'),))
		question = QQuestion( parts=(part,) )
		assert_that(hash(question), is_(hash(question)))
		assert_that(question, is_(question))
		component.provideUtility( question, provides=interfaces.IQuestion,  name="1")

		sub = submission.QuestionSubmission( questionId="1", parts=('correct',) )

		result = interfaces.IQAssessedQuestion( sub )
		assert_that( result, has_property( 'questionId', "1" ) )
		assert_that( result, has_property( 'parts', contains( assessed.QAssessedPart( submittedResponse='correct', assessedValue=1.0 ) ) ) )

		_check_old_dublin_core( result )

	def test_assess_with_null_part(self):
		# A null part means no answer was provided
		part = parts.QFreeResponsePart(solutions=(solutions.QFreeResponseSolution(value='correct'),))
		question = QQuestion( parts=(part,) )
		component.provideUtility( question, provides=interfaces.IQuestion,  name="1")

		sub = submission.QuestionSubmission( )
		internalization.update_from_external_object( sub, {'questionId':"1", 'parts': [None]},
													 notify=False)

		result = interfaces.IQAssessedQuestion( sub )
		assert_that( result, has_property( 'questionId', "1" ) )
		assert_that( result, has_property( 'parts',
										   contains( assessed.QAssessedPart(
											   submittedResponse=None,
											   assessedValue=0.0 ) ) ) )

		_check_old_dublin_core( result )

	def test_assess_with_incorrect_part(self):
		# An incorrect part raises a useful validation error
		part = parts.QFreeResponsePart(solutions=(solutions.QFreeResponseSolution(value='correct'),))
		question = QQuestion( parts=(part,) )
		component.provideUtility( question, provides=interfaces.IQuestion,  name="1")

		sub = submission.QuestionSubmission( )
		internalization.update_from_external_object( sub, {'questionId':"1", 'parts': [[]]},
													 notify=False)

		assert_that( calling( interfaces.IQAssessedQuestion ).with_args(sub),
					 raises(InvalidValue))

	def test_assess_with_incorrect_multichoice_part(self):
		part = parts.QMultipleChoicePart(solutions=(solutions.QMultipleChoiceSolution(value=1),))
		question = QQuestion( parts=(part,) )
		assert_that(hash(question), is_(hash(question)))
		assert_that(question, is_(question))

		component.provideUtility( question, provides=interfaces.IQuestion,  name="1")

		sub = submission.QuestionSubmission( )
		internalization.update_from_external_object( sub, {'questionId':"1", 'parts': ['']},
													 notify=False)

		assert_that( calling( interfaces.IQAssessedQuestion ).with_args(sub),
					 raises(InvalidValue))

	def test_assess_with_incorrect_float_part(self):
		part = parts.QNumericMathPart(solutions=(solutions.QNumericMathSolution(value=1),))
		question = QQuestion( parts=(part,) )
		component.provideUtility( question, provides=interfaces.IQuestion,  name="1")

		sub = submission.QuestionSubmission( )
		internalization.update_from_external_object( sub, {'questionId':"1", 'parts': ['']},
													 notify=False)

		assert_that( calling( interfaces.IQAssessedQuestion ).with_args(sub),
					 raises(InvalidValue))

	def test_assess_with_file_part(self):
		part = parts.QFilePart()
		part.allowed_mime_types = ('*/*',)
		part.allowed_extensions = '*'
		question = QQuestion( parts=(part,) )

		component.provideUtility( question, provides=interfaces.IQuestion,  name="1")

		sub = submission.QuestionSubmission( questionId="1", parts=('correct',) )
		# Wrong submission type, cannot be assessed at all
		assert_that( calling( interfaces.IQAssessedQuestion ).with_args(sub),
					 raises( TypeError ))

		# Right submission type, but not a valid submission
		sub = submission.QuestionSubmission( questionId="1", parts=(response.QUploadedFile(),) )
		assert_that( calling( interfaces.IQAssessedQuestion ).with_args(sub),
					 raises( interface.Invalid ))

		sub = submission.QuestionSubmission( questionId="1", parts=(response.QUploadedFile(data=b'1234',
																						   contentType=b'text/plain',
																						   filename='foo.txt'),) )
		result = interfaces.IQAssessedQuestion( sub )
		assert_that( result, has_property( 'questionId', "1" ) )
		assert_that( result, has_property( 'parts', contains( assessed.QAssessedPart( submittedResponse=sub.parts[0],
																					  assessedValue=None ) ) ) )
		assert_that( sub.parts[0], has_property( 'lastModified', greater_than(0) ) )
		assert_that( sub.parts[0], has_property( 'createdTime', greater_than(0) ) )

		# Now if the part gets constraints on filename or mimeType or size
		# submission can fail
		part.allowed_mime_types = ('application/octet-stream',)
		assert_that( calling( interfaces.IQAssessedQuestion ).with_args(sub),
					 raises( interface.Invalid, 'mimeType' ))

		part.allowed_mime_types = ('*/*',)
		part.allowed_extensions = ('.doc',)
		assert_that( calling( interfaces.IQAssessedQuestion ).with_args(sub),
					 raises( interface.Invalid, 'filename' ))

		part.allowed_extensions = '*'
		part.max_file_size = 0
		assert_that( calling( interfaces.IQAssessedQuestion ).with_args(sub),
					 raises( interface.Invalid, 'max_file_size' ))

	def test_assess_with_modeled_content_part(self):
		part = parts.QModeledContentPart()
		question = QQuestion( parts=(part,) )

		component.provideUtility( question, provides=interfaces.IQuestion,  name="1")

		sub = submission.QuestionSubmission( questionId="1", parts=('correct',) )
		# Wrong submission type, cannot be assessed at all
		assert_that(calling(interfaces.IQAssessedQuestion).with_args(sub),
		 			raises(TypeError))

		# Right submission type, but not a valid submission
		sub = submission.QuestionSubmission( questionId="1", parts=(response.QModeledContentResponse(),) )
		assert_that( calling( interfaces.IQAssessedQuestion ).with_args(sub),
					 raises( interface.Invalid ))

		sub = submission.QuestionSubmission( questionId="1", parts=(response.QModeledContentResponse(value=['a part']),) )

		result = interfaces.IQAssessedQuestion( sub )
		assert_that( result, has_property( 'questionId', "1" ) )
		assert_that( result, has_property( 'parts', contains( assessed.QAssessedPart( submittedResponse=sub.parts[0],
																					  assessedValue=None ) ) ) )

class TestAssessedQuestionSet(AssessmentTestCase):

	def test_externalizes(self):
		assert_that( assessed.QAssessedQuestionSet(), verifiably_provides( interfaces.IQAssessedQuestionSet ) )
		assert_that( assessed.QAssessedQuestionSet(), verifiably_provides( ILastModified ) )
		assert_that( assessed.QAssessedQuestionSet(), externalizes( has_entries( 'Class', 'AssessedQuestionSet',
																				 'MimeType', 'application/vnd.nextthought.assessment.assessedquestionset') ) )
		assert_that( internalization.find_factory_for( toExternalObject( assessed.QAssessedQuestionSet() ) ),
					 is_( none() ) )

	def test_assess(self):
		part = parts.QFreeResponsePart(solutions=(solutions.QFreeResponseSolution(value='correct'),))
		question = QQuestion( parts=(part,) )
		question_set = QQuestionSet( questions=(question,) )

		component.provideUtility( question,
								  provides=interfaces.IQuestion,
								  name="1" )
		component.provideUtility( question_set,
								  provides=interfaces.IQuestionSet,
								  name="2" )

		sub = submission.QuestionSubmission( questionId="1", parts=('correct',) )
		set_sub = submission.QuestionSetSubmission( questionSetId="2", questions=(sub,) )

		result = interfaces.IQAssessedQuestionSet( set_sub )

		assert_that( result, has_property( 'questionSetId', "2" ) )
		assert_that( result, has_property( 'questions',
										   contains(
											   has_property( 'parts', contains( assessed.QAssessedPart( submittedResponse='correct', assessedValue=1.0 ) ) ) ) ) )
		# consistent hashing
		assert_that( hash(result), is_(hash(result)))
		
		for question in result.questions:
			parents = list(lineage(question))
			assert_that(parents, has_length(1))
		
		ext_obj = toExternalObject( result )
		assert_that( ext_obj, has_entry( 'questions', has_length( 1 ) ) )

		_check_old_dublin_core( result )
		
		for question in result.questions:
			parents = list(lineage(question))
			assert_that(parents[-1], is_(result))
			assert_that(parents, has_length(greater_than(1)))
			for part in question.parts:
				parents = list(lineage(part))
				assert_that(parents, has_length(greater_than(2)))
				assert_that(parents[-1], is_(result))

	def test_assess_not_same_instance_question_but_id_matches(self):
		part = parts.QFreeResponsePart(solutions=(solutions.QFreeResponseSolution(value='correct'),))
		question = QQuestion( parts=(part,) )
		question.ntiid = 'abc'
		question_set = QQuestionSet( questions=(question,) )

		component.provideUtility( question,
								  provides=interfaces.IQuestion,
								  name='abc')
		component.provideUtility( question_set,
								  provides=interfaces.IQuestionSet,
								  name="2" )
		# New instance
		part = parts.QFreeResponsePart(solutions=(solutions.QFreeResponseSolution(value='correct2'),))
		question = QQuestion( parts=(part,) )
		question.ntiid = 'abc'

		component.provideUtility( question,
								  provides=interfaces.IQuestion,
								  name='abc')

		assert_that( question, is_not( question_set.questions[0] ) )

		sub = submission.QuestionSubmission( questionId='abc', parts=('correct2',) )
		set_sub = submission.QuestionSetSubmission( questionSetId="2", questions=(sub,) )

		result = interfaces.IQAssessedQuestionSet( set_sub )

		assert_that( result, has_property( 'questionSetId', "2" ) )
		assert_that( result, has_property( 'questions',
										   contains(
											   has_property( 'parts', contains( assessed.QAssessedPart( submittedResponse='correct2', assessedValue=1.0 ) ) ) ) ) )


		ext_obj = toExternalObject( result )
		assert_that( ext_obj, has_entry( 'questions', has_length( 1 ) ) )

	def test_assess_not_same_instance_question_but_equals(self):
		part = parts.QFreeResponsePart(solutions=(solutions.QFreeResponseSolution(value='correct'),))
		question = QQuestion( content='foo', parts=(part,) )
		question_set = QQuestionSet( questions=(question,) )

		# New instance
		part = parts.QFreeResponsePart(solutions=(solutions.QFreeResponseSolution(value='correct'),))
		question = QQuestion( content='foo', parts=(part,) )

		assert_that( question, is_( question_set.questions[0] ) )
		# Some quick coverage things
		assert_that( hash( question ), is_( hash( question_set.questions[0] ) ) )
		hash( question_set )
		assert_that( question != question, is_false() )
		assert_that( question_set != question_set, is_false() )

		component.provideUtility( question,
								  provides=interfaces.IQuestion,
								  name="abc" )
		component.provideUtility( question_set,
								  provides=interfaces.IQuestionSet,
								  name="2")

		sub = submission.QuestionSubmission( questionId='abc', parts=('correct',) )
		set_sub = submission.QuestionSetSubmission( questionSetId="2", questions=(sub,) )

		result = interfaces.IQAssessedQuestionSet( set_sub )

		assert_that( result, has_property( 'questionSetId', "2" ) )
		assert_that( result, has_property( 'questions',
										   contains(
											   has_property( 'parts', contains( assessed.QAssessedPart( submittedResponse='correct', assessedValue=1.0 ) ) ) ) ) )


		ext_obj = toExternalObject( result )
		assert_that( ext_obj, has_entry( 'questions', has_length( 1 ) ) )
