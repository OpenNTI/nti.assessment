#!/usr/bin/env python
"""
$Id$
"""
from __future__ import print_function, unicode_literals

from hamcrest import assert_that, has_entry, is_, has_property, contains, same_instance
from hamcrest import has_key
from hamcrest import not_none
from unittest import TestCase
from nti.testing.matchers import verifiably_provides
from nti.externalization.tests import externalizes
from nose.tools import assert_raises

from zope import component
from zope.schema import interfaces as sch_interfaces
from zope.dottedname import resolve as dottedname

import nti.assessment
from nti.externalization.externalization import toExternalObject
from nti.externalization.internalization import update_from_external_object
from nti.externalization import internalization
from nti.externalization import interfaces as ext_interfaces

from nti.assessment import interfaces
from nti.assessment import submission


# nose module-level setup
setUpModule = lambda: nti.testing.base.module_setup( set_up_packages=(nti.assessment,) )
tearDownModule = nti.testing.base.module_teardown


class TestQuestionSubmission(TestCase):

	def test_externalizes(self):
		assert_that( submission.QuestionSubmission(), verifiably_provides( interfaces.IQuestionSubmission ) )
		assert_that( submission.QuestionSubmission(), externalizes( has_entry( 'Class', 'QuestionSubmission' ) ) )
		assert_that( internalization.find_factory_for( toExternalObject( submission.QuestionSubmission() ) ),
					 is_( same_instance( submission.QuestionSubmission ) ) )


		# Now verify the same for the mimetype-only version
		mtd = dottedname.resolve( 'nti.mimetype.externalization.MimeTypeDecorator' )
		component.provideSubscriptionAdapter( mtd, provides=ext_interfaces.IExternalMappingDecorator )
		assert_that( submission.QuestionSubmission(), externalizes( has_key( 'MimeType' ) ) )
		ext_obj_no_class = toExternalObject( submission.QuestionSubmission() )
		ext_obj_no_class.pop( 'Class' )

		assert_that( internalization.find_factory_for( ext_obj_no_class ),
					 is_( not_none() ) )


		# No coersion of parts happens yet at this level
		submiss = submission.QuestionSubmission()
		with assert_raises(sch_interfaces.RequiredMissing):
			update_from_external_object( submiss, {"parts": ["The text response"]}, require_updater=True )

		update_from_external_object( submiss, {'questionId': 'foo', "parts": ["The text response"]}, require_updater=True )
		assert_that( submiss, has_property( "parts", contains( "The text response" ) ) )

class TestQuestionSetSubmission(TestCase):

	def test_externalizes(self):
		assert_that( submission.QuestionSetSubmission(), verifiably_provides( interfaces.IQuestionSetSubmission ) )
		assert_that( submission.QuestionSetSubmission(), externalizes( has_entry( 'Class', 'QuestionSetSubmission' ) ) )

		qss = submission.QuestionSetSubmission()
		with assert_raises(sch_interfaces.RequiredMissing):
			update_from_external_object( qss, {}, require_updater=True )

		# Wrong type for objects in questions
		with assert_raises(sch_interfaces.WrongContainedType):
			update_from_external_object( qss, {'questionSetId': 'foo',
											   "questions": ["The text response"]}, require_updater=True )

		# Validation is recursive
		with assert_raises( sch_interfaces.WrongContainedType) as wct:
			update_from_external_object( qss, {'questionSetId': 'foo',
											   "questions": [submission.QuestionSubmission()]}, require_updater=True )

		assert_that( wct.exception.args[0][0], is_( sch_interfaces.WrongContainedType ) )

		update_from_external_object( qss, {'questionSetId': 'foo',
										   "questions": [submission.QuestionSubmission(questionId='foo', parts=[])]}, require_updater=True )

		assert_that( qss, has_property( 'questions', contains( is_( submission.QuestionSubmission ) ) ) )
