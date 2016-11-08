#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import assert_that

from nti.assessment.interfaces import IQPoll
from nti.assessment.interfaces import IQSurvey
from nti.assessment.interfaces import IQuestion
from nti.assessment.interfaces import IQuestionSet
from nti.assessment.interfaces import IQAssignment
from nti.assessment.interfaces import IQTimedAssignment

from nti.assessment.randomized.interfaces import IQuestionBank
from nti.assessment.randomized.interfaces import IRandomizedQuestionSet

from nti.assessment import ASSESSMENT_INTERFACES

from nti.assessment.tests import AssessmentTestCase

class TestAssessedPart(AssessmentTestCase):

	def test_interfaces(self):
		ifaces = (# order matters
				IQPoll,
				IQuestion,
				IQSurvey,
				IQuestionBank,
				IQuestionSet,
				IQTimedAssignment,
				IQAssignment
		)
		assert_that(ASSESSMENT_INTERFACES, is_(ifaces))
