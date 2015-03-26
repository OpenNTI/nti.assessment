#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import assert_that
from hamcrest import has_property

from zope import component

from nti.externalization.externalization import toExternalObject
from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

from nti.assessment.interfaces import IQPoll
from nti.assessment.interfaces import IQSurvey
from nti.assessment.interfaces import IQNonGradableMultipleChoicePart

from nti.assessment.parts import QNonGradableFreeResponsePart
from nti.assessment.parts import QNonGradableMultipleChoicePart

from nti.assessment.poll import QPoll
from nti.assessment.poll import QSurvey
from nti.assessment.poll import QPollSubmission

from nti.externalization.tests import externalizes

from nti.testing.matchers import verifiably_provides

from nti.assessment.tests import AssessmentTestCase

class TestPolls(AssessmentTestCase):

	def test_part_provides(self):
		assert_that( QNonGradableMultipleChoicePart(), 
					 verifiably_provides(IQNonGradableMultipleChoicePart ) )

		assert_that( QNonGradableMultipleChoicePart(),
					 externalizes( has_entry( 'Class', 'NonGradableMultipleChoicePart' ) ) )

		part = QNonGradableMultipleChoicePart( choices=list(("A", "B", "C")) )
		assert_that( part, verifiably_provides( IQNonGradableMultipleChoicePart ) )
		assert_that( part, is_( part ) )
		assert_that( hash(part), is_( hash(part) ) )

	def test_externalizes(self):
		part = QNonGradableFreeResponsePart()
		poll = QPoll( parts=(part,) )
		
		assert_that( poll, verifiably_provides( IQPoll ) )
		assert_that( find_factory_for( toExternalObject( poll ) ),
					 is_not( none() ) )
		
		survery = QSurvey(questions=(poll,))
		assert_that( survery, verifiably_provides( IQSurvey ) )
		assert_that( find_factory_for( toExternalObject( survery ) ),
					 is_not( none() ) )

	def test_submitted_with_null_part(self):
		part = QNonGradableFreeResponsePart()
		question = QPoll( parts=(part,) )
		component.provideUtility( question, provides=IQPoll,  name="1")

		sub = QPollSubmission( )
		update_from_external_object( sub, {'pollId':"1", 'parts': [None]},
									 notify=False)

		assert_that( sub, has_property( 'pollId', "1" ) )
		assert_that( sub, has_property( 'parts', is_([None])) )
