#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import has_entries
from hamcrest import assert_that
does_not = is_not

import os

from nti.assessment import parts
from nti.assessment import question
from nti.assessment import assignment
from nti.assessment import interfaces
from nti.assessment.common import hashfile
from nti.assessment.common import signature

from nti.assessment.tests import AssessmentTestCase

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

from nti.externalization.tests import externalizes

class TestAssignment(AssessmentTestCase):

	def test_externalizes(self):
		assert_that( assignment.QAssignmentPart(), verifiably_provides( interfaces.IQAssignmentPart ) )
		# But missing a question set
		assert_that( assignment.QAssignmentPart(), does_not( validly_provides( interfaces.IQAssignmentPart ) ) )
		assert_that( assignment.QAssignmentPart(), externalizes( has_entry( 'Class', 'AssignmentPart' ) ) )

		part = assignment.QAssignmentPart(
			question_set=question.QQuestionSet(
				questions=[question.QQuestion(
					parts=[parts.QMathPart()])]) )
		assert_that( part, validly_provides( interfaces.IQAssignmentPart ) )

		assert_that( assignment.QAssignment(), verifiably_provides( interfaces.IQAssignment ) )
		# This is now valid since we default to empty parts.
		assert_that( assignment.QAssignment(), validly_provides( interfaces.IQAssignment ) )
		assert_that( assignment.QAssignment(), externalizes( has_entries( 'Class', 'Assignment',
																		  'category_name', 'default',
																		  'CategoryName', 'default',
																		  'no_submit', False,
																		  'NoSubmit', False) ) )

		assert_that( assignment.QAssignment(parts=[part]),
					 validly_provides(interfaces.IQAssignment) )

		assert_that( assignment.QAssignmentSubmissionPendingAssessment(),
					 verifiably_provides( interfaces.IQAssignmentSubmissionPendingAssessment ))
		assert_that( assignment.QAssignmentSubmissionPendingAssessment(),
					 externalizes( has_entry( 'Class', 'AssignmentSubmissionPendingAssessment' )))

	def test_signature(self):
		a = assignment.QAssignment()
		a.lastModified = a.createdTime = 0
		assert_that(signature(a),
					is_('43e4476f3e9dbd9a3f1a4ea108080069c5b7bdc8998b1c1945b3d4fa719397fd') )

		path = os.path.join(os.path.dirname(__file__), "questionbank.json")
		with open(path, "rb") as fp:
			assert_that(hashfile(fp),
						is_('711d848c5536cfcd7a5aae4b638aa71fb94ead061be996fe784aa18e1aadffd5') )
