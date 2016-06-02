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
does_not = is_not

from nti.testing.matchers import verifiably_provides

from nti.assessment.common import QSubmittedPart
from nti.assessment.common import grader_for_solution_and_response

from nti.assessment.interfaces import IQTextResponse
from nti.assessment.interfaces import IQSubmittedPart
from nti.assessment.interfaces import IQMultipleChoicePartGrader

from nti.assessment.parts import QMultipleChoicePart

from nti.assessment.randomized.interfaces import IQRandomizedMultipleChoicePartGrader


from nti.assessment.solution import QMultipleChoiceSolution

from nti.externalization.externalization import toExternalObject

from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

from nti.assessment.tests import AssessmentTestCase

from nti.externalization.tests import externalizes

class TestCommon(AssessmentTestCase):

	def test_submitted_part(self):
		assert_that(QSubmittedPart(), verifiably_provides(IQSubmittedPart))
		assert_that(QSubmittedPart(), externalizes(has_entry('Class', 'SubmittedPart')))
		assert_that(find_factory_for(toExternalObject(QSubmittedPart())),
					is_(none()))

		part = QSubmittedPart()
		update_from_external_object(part, {"submittedResponse": "The text response"},
									require_updater=True)

		assert_that(part.submittedResponse, is_("The text response"))

		part = QSubmittedPart(submittedResponse=[1, 2, 3])
		hash(part)
		assert_that(part, is_(part))

	def test_grader(self):
		part = QMultipleChoicePart()
		solution = QMultipleChoiceSolution(value=1)
		response = IQTextResponse('1')
		grader1 = grader_for_solution_and_response(part, solution, response)
		assert_that(grader1, verifiably_provides(IQMultipleChoicePartGrader))
		assert_that(grader1, does_not(verifiably_provides(IQRandomizedMultipleChoicePartGrader)))

		part.randomized = True
		grader2 = grader_for_solution_and_response(part, solution, response)
		assert_that(grader2, verifiably_provides(IQRandomizedMultipleChoicePartGrader))
