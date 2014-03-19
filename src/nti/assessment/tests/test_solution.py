#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import assert_that

from unittest import TestCase

from zope import interface

from nti.assessment import solution, response
from nti.assessment import interfaces

from nti.externalization.externalization import toExternalObject

from nti.assessment.tests import grades_right
from nti.assessment.tests import grades_wrong
grades_correct = grades_right

import nti.testing.base
from nti.testing.matchers import is_true, is_false
from nti.testing.matchers import verifiably_provides

# nose module-level setup
setUpModule = lambda: nti.testing.base.module_setup( set_up_packages=(__name__,) )
tearDownModule = nti.testing.base.module_teardown

class TestConvert(TestCase):

	def test_not_isolution(self):
		assert_that( interfaces.convert_response_for_solution( self, self ), is_( self ) )
		# Because we have no interfaces, no conversion is attempted
		assert_that( interfaces.convert_response_for_solution( self, 42 ), is_( 42 ) )

	def test_convert_fails(self):
		class Soln(object):
			interface.implements(interfaces.IQMathSolution)

		assert_that( interfaces.convert_response_for_solution( Soln(), self ), is_( self ) )

	def test_convert_from_string(self):
		class Soln(object):
			interface.implements(interfaces.IQMathSolution)

		assert_that( interfaces.convert_response_for_solution( Soln(), "string" ), is_( response.QTextResponse ) )

	def test_convert_from_number(self):
		class Soln(object):
			interface.implements(interfaces.IQNumericMathSolution)

		assert_that( interfaces.convert_response_for_solution( Soln(), 42 ), is_( response.QTextResponse ) )

class TestNumericMathSolution(TestCase):

	def test_grade_numbers(self):
		assert_that( solution.QNumericMathSolution( 1 ), verifiably_provides( interfaces.IQNumericMathSolution ) )

		assert_that( solution.QNumericMathSolution( 1 ).grade( "1" ), is_true( ) )
		assert_that( solution.QNumericMathSolution( 1.0 ).grade( "1" ), is_true( ) )
		assert_that( solution.QNumericMathSolution( 1.0 ).grade( "1.0" ), is_true( ) )
		assert_that( solution.QNumericMathSolution( 1 ).grade( "1.0" ), is_true( ) )
		# via number-to-text-solution-to-number
		assert_that( solution.QNumericMathSolution( 1 ).grade( 1 ), is_true( ) )
		assert_that( solution.QNumericMathSolution( 1 ).grade( 1.2 ), is_false( ) )

	def test_grade_units( self ):
		forbidden = solution.QNumericMathSolution( 1, () )
		required = solution.QNumericMathSolution( 1, ('cm',) )
		optional = solution.QNumericMathSolution( 1, ('cm', '' ) )

		assert_that( forbidden, grades_right( "1" ) )
		assert_that( forbidden, grades_right( " 1.0 " ) )
		assert_that( forbidden, grades_right( "1.0" ) )
		assert_that( forbidden, grades_wrong( "1 cm" ) )
		assert_that( forbidden, grades_wrong( "1.0cm" ) )

		assert_that( required, grades_wrong( "1" ) )
		assert_that( required, grades_wrong( " 1.0 " ) )
		assert_that( required, grades_wrong( "1.0" ) )
		assert_that( required, grades_right( "1 cm" ) )
		assert_that( required, grades_right( "1.0cm" ) )

		assert_that( optional, grades_right( "1" ) )
		assert_that( optional, grades_right( " 1.0 " ) )
		assert_that( optional, grades_right( "1.0" ) )
		assert_that( optional, grades_right( "1 cm" ) )
		assert_that( optional, grades_right( "1.0cm" ) )

	def test_external_units( self ):
		default = solution.QNumericMathSolution( 1 )
		forbidden = solution.QNumericMathSolution( 1, () )
		required = solution.QNumericMathSolution( 1, ('cm',) )
		optional = solution.QNumericMathSolution( 1, ('cm', '' ) )

		ext = toExternalObject( default )
		assert_that( ext, has_entry( 'allowed_units', None ) )

		ext = toExternalObject( forbidden )
		assert_that( ext, has_entry( 'allowed_units', [] ) )

		ext = toExternalObject( required )
		assert_that( ext, has_entry( 'allowed_units', ['cm'] ) )

		ext = toExternalObject( optional )
		assert_that( ext, has_entry( 'allowed_units', ['cm', ''] ) )


	def test_equality( self ):
		soln = solution.QNumericMathSolution( 1 )
		soln2 = solution.QNumericMathSolution( 1 )
		soln3 = solution.QNumericMathSolution( 2 )

		soln4 = solution.QNumericMathSolution( 1 )
		soln4.weight = 0.5

		assert_that( soln, is_( soln2 ) )
		assert_that( soln, is_not( soln3 ) )
		assert_that( soln, is_not( soln4 ) )
		assert soln != soln4 # hit the ne operator

class TestFreeResponseSolution(TestCase):

	def test_grade_simple_string(self):
		assert_that( solution.QFreeResponseSolution( "text" ), grades_correct( "text" ) )

	def test_grade_string_case_insensitive( self ):
		# SAJ: We are now not case sensitive
		assert_that( solution.QFreeResponseSolution( "text" ), grades_correct( "Text" ) )

	def test_grade_string_quote_replacement(self):

		solution_text = "“Today” ‘what’"  # Note both double and single curly quotes
		response_text = "\"Today\" 'what'"

		assert_that( solution.QFreeResponseSolution( solution_text ),
					grades_correct( response_text ) )

class TestMultipleChoiceMultipleAnswerSolution(TestCase):

	def test_multiplechoicemultipleanswersolution(self):
		assert_that( solution.QMultipleChoiceMultipleAnswerSolution( [ 1 ] ), grades_correct( [ 1 ] ) )
		assert_that( solution.QMultipleChoiceMultipleAnswerSolution( [ 1, 2 ] ), grades_correct( [ 1, 2 ] ) )
		assert_that( solution.QMultipleChoiceMultipleAnswerSolution( [ 1, 2, 3 ] ), grades_correct( [ 1, 2, 3 ] ) )
		assert_that( solution.QMultipleChoiceMultipleAnswerSolution( [ 1, 2 ] ), grades_wrong( [2, 1] ) )

class TestFillInTheBlankWithWordBankSolution(TestCase):

	def test_solution(self):
		assert_that(solution.QFillInTheBlankWithWordBankSolution([ '1' ]),
					verifiably_provides(interfaces.IQFillInTheBlankWithWordBankSolution))
		assert_that(solution.QFillInTheBlankWithWordBankSolution([ '1' ]).grade([ '1' ]), is_(1.0))

class TestFillInTheBlankWithShortAnswerSolution(TestCase):

	def test_solution(self):
		regex = solution.RegularExpression(pattern="^1$")
		assert_that(solution.QFillInTheBlankShortAnswerSolution([regex]),
					verifiably_provides(interfaces.IQFillInTheBlankShortAnswerSolution))
		assert_that(solution.QFillInTheBlankShortAnswerSolution([regex]).grade(['1']), is_(1.0))
		assert_that(solution.QFillInTheBlankShortAnswerSolution([regex]).grade(['2']), is_(0))
		assert_that(solution.QFillInTheBlankShortAnswerSolution([regex]).grade(['11']), is_(0))
		assert_that(solution.QFillInTheBlankShortAnswerSolution([regex]).grade(['121']), is_(0))
