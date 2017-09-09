#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import all_of
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import assert_that
from hamcrest import has_entries

from nose.tools import assert_raises

from nti.testing.matchers import is_true
from nti.testing.matchers import is_false
from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

from zope import interface

from nti.assessment import parts
from nti.assessment import wordbank
from nti.assessment import interfaces
from nti.assessment import solution as solutions

from nti.assessment.tests import grades_right
from nti.assessment.tests import grades_wrong

from nti.assessment.tests import AssessmentTestCase

from nti.externalization.tests import externalizes


class TestQPart(AssessmentTestCase):

    def test_part_provides(self):
        part = parts.QPart()
        assert_that(part, verifiably_provides(interfaces.IQPart))
        assert_that(part, is_(part))
        assert_that(part, is_not(parts.QPart(content=u'other')))
        # hit the ne operator specifically
        assert part != parts.QPart(content=u'other')

    def test_part_badkw(self):
        with assert_raises(TypeError):
            parts.QPart(bad_kw=1)


class TestMultipleChoicePart(AssessmentTestCase):

    def test_part_provides(self):
        assert_that(parts.QMultipleChoicePart(), 
                    verifiably_provides(interfaces.IQMultipleChoicePart))
        assert_that(parts.QMultipleChoicePart(), 
                    externalizes(has_entry('Class', 'MultipleChoicePart')))

        # A bad solution type
        part = parts.QMultipleChoicePart(solutions=(u"foo",))
        assert_that(part, verifiably_provides(interfaces.IQMultipleChoicePart))
        assert_that(part, is_(part))
        assert_that(hash(part), is_(hash(part)))

        with assert_raises(interface.Invalid):
            sf = interfaces.IQMultipleChoicePart['solutions']
            sf.bind(part)
            sf.validate(part.solutions)

    def test_grade(self):
        solution = solutions.QMultipleChoiceSolution(1)
        choices = (u"A", u"B", u"C")
        part = parts.QMultipleChoicePart(solutions=(solution,),
                                         choices=list(choices))
        assert_that(hash(part), is_(hash(part)))

        # Submitting the actual data
        assert_that(part.grade(u"B"), is_true())
        assert_that(part.grade(u"A"), is_false())

        # Submitting the index
        assert_that(part.grade(1), is_true())
        assert_that(part.grade(0), is_false())


class TestMultipleChoiceMultipleAnswerPart(AssessmentTestCase):

    def test_part_provides(self):
        assert_that(parts.QMultipleChoiceMultipleAnswerPart(), 
                    verifiably_provides(interfaces.IQMultipleChoiceMultipleAnswerPart))
        assert_that(parts.QMultipleChoiceMultipleAnswerPart(), 
                    externalizes(has_entry('Class', 'MultipleChoiceMultipleAnswerPart')))

        # A bad solution type
        part = parts.QMultipleChoiceMultipleAnswerPart(solutions=([0, 1],))
        assert_that(part, 
                    verifiably_provides(interfaces.IQMultipleChoiceMultipleAnswerPart))
        assert_that(part, is_(part))
        assert_that(hash(part), is_(hash(part)))

        with assert_raises(interface.Invalid):
            sf = interfaces.IQMultipleChoiceMultipleAnswerPart['solutions']
            sf.bind(part)
            sf.validate(part.solutions)

    def test_grade(self):
        solution = solutions.QMultipleChoiceMultipleAnswerSolution([1])
        choices = (u"A", u"B", u"C")
        part = parts.QMultipleChoiceMultipleAnswerPart(solutions=(solution,), 
                                                       choices=choices)

        # Submitting the index
        assert_that(part.grade([1]), is_true())
        assert_that(part.grade([0]), is_false())


class TestMatchingPart(AssessmentTestCase):

    def test_grade(self):
        labels = (u"A", u"B")
        values = (u"X", u"Y")

        solution_keys = {u"A": u"Y", u"B": u"X"}
        solution_nums = {0: 1, 1: 0}

        solution = solutions.QMatchingSolution(solution_keys)
        part = parts.QMatchingPart(labels=labels, values=values, 
                                   solutions=(solution,))
        part2 = parts.QMatchingPart(labels=labels, values=values, 
                                    solutions=(solution,))
        assert_that(part, externalizes(has_entry('Class', 'MatchingPart')))
        assert_that(part, is_(part))
        assert_that(part, is_(part2))
        assert_that(hash(part), is_(hash(part)))

        assert_that(part, grades_right(solution_keys))
        assert_that(part, grades_right(solution_nums))

        assert_that(part, grades_wrong({"A": "Y"}))

        part = parts.QMatchingPart(labels=labels, values=values, 
                                   solutions=(solutions.QMatchingSolution(solution_nums),))

        assert_that(part, grades_right(solution_keys))
        assert_that(part, grades_right(solution_nums))

        assert_that(part, grades_wrong({"A": "Y"}))

        assert_that(part, grades_wrong({"A": "Z"}))

    def test_eq(self):
        labels = (u"A", u"B")
        values = (u"X", u"Y")

        solution_keys = {u"A": u"Y", u"B": u"X"}

        solution = solutions.QMatchingSolution(solution_keys)
        part = parts.QMatchingPart(labels=labels, values=values, 
                                   solutions=(solution,))
        part2 = parts.QMatchingPart(labels=labels, values=values, 
                                    solutions=(solution,))

        assert_that(part, is_(part))
        assert_that(part, is_(part2))
        assert_that(part, 
                    is_not(parts.QMatchingPart(labels=values, values=labels, 
                                               solutions=(solution,))))
        assert_that(part, 
                    is_not(parts.QNumericMathPart(solutions=(solution,))))
        assert_that(parts.QNumericMathPart(solutions=(solution,)), 
                    is_not(part))

        # Cover the AttributeError case
        qnp = parts.QNumericMathPart(solutions=(solution,))
        qnp.grader_interface = part.grader_interface
        assert_that(part, is_not(qnp))

        assert_that(hash(part), is_(hash(part2)))


class TestOrderingPart(AssessmentTestCase):

    def test_grade(self):
        labels = (u"A", u"B")
        values = (u"X", u"Y")
        solution_nums = {0: 1, 1: 0}
        solution_keys = {u"A": u"Y", u"B": u"X"}

        solution = solutions.QOrderingSolution(solution_keys)
        part = parts.QOrderingPart(labels=labels, values=values, 
                                   solutions=(solution,))
        part2 = parts.QOrderingPart(labels=labels, values=values, 
                                    solutions=(solution,))
        assert_that(part, 
                    externalizes(all_of(has_entry('Class', 'OrderingPart'),
                                        has_entry('MimeType', 'application/vnd.nextthought.assessment.orderingpart'))))
        assert_that(part, is_(part))
        assert_that(part, is_(part2))
        assert_that(hash(part), is_(hash(part)))

        assert_that(part, grades_right(solution_keys))
        assert_that(part, grades_right(solution_nums))

        assert_that(part, grades_wrong({"A": "Y"}))

        part = parts.QOrderingPart(labels=labels,
                                   values=values,
                                   solutions=(solutions.QOrderingSolution(solution_nums),))

        assert_that(part, grades_right(solution_keys))
        assert_that(part, grades_right(solution_nums))
        assert_that(part, grades_wrong({"A": "Y"}))
        assert_that(part, grades_wrong({"A": "Z"}))

    def test_eq(self):
        labels = (u"A", u"B")
        values = (u"X", u"Y")
        solution_keys = {u"A": u"Y", u"B": u"X"}

        solution = solutions.QOrderingSolution(solution_keys)
        part = parts.QOrderingPart(labels=labels, values=values, 
                                   solutions=(solution,))
        part2 = parts.QOrderingPart(labels=labels, values=values, 
                                    solutions=(solution,))

        assert_that(part, is_(part))
        assert_that(part, is_(part2))
        assert_that(part, 
                    is_not(parts.QOrderingPart(labels=values, values=labels, 
                                               solutions=(solution,))))
        assert_that(part, 
                    is_not(parts.QNumericMathPart(solutions=(solution,))))
        assert_that(parts.QNumericMathPart(solutions=(solution,)), 
                    is_not(part))

        # Cover the AttributeError case
        qnp = parts.QNumericMathPart(solutions=(solution,))
        qnp.grader_interface = part.grader_interface
        assert_that(part, is_not(qnp))

        assert_that(hash(part), is_(hash(part2)))


class TestFillInTheBlackWithWordBankPart(AssessmentTestCase):

    def test_grade(self):
        entries = [wordbank.WordEntry(wid=u'1', word=u'bankai'),
                   wordbank.WordEntry(wid=u'2', word=u'shikai')]
        bank = wordbank.WordBank(entries=entries, unique=True)
        solution = solutions.QFillInTheBlankWithWordBankSolution(
            {u"x": u"1", u"y": u"2"}
        )
        part = parts.QFillInTheBlankWithWordBankPart(wordbank=bank, 
                                                     solutions=(solution,))
        assert_that(part,
                    verifiably_provides(interfaces.IQFillInTheBlankWithWordBankPart))
        assert_that(part, 
                    externalizes(has_entry('Class', 'FillInTheBlankWithWordBankPart')))
        assert_that(solution.grade({"x": "1", "y": "2"}), is_(True))
        assert_that(solution.grade({"x": "1", "y": "4"}), is_(False))


class TestFillInTheBlackShortAnswerPart(AssessmentTestCase):

    def test_external(self):
        solution = solutions.QFillInTheBlankShortAnswerSolution({'x': "^1$"})
        part = parts.QFillInTheBlankShortAnswerPart(solutions=(solution,))
        assert_that(part,
                    verifiably_provides(interfaces.IQFillInTheBlankShortAnswerPart))
        assert_that(part, 
                    externalizes(has_entry('Class', 'FillInTheBlankShortAnswerPart')))
        assert_that(solution, 
                    externalizes(has_entries('Class', 'FillInTheBlankShortAnswerSolution',
                                             'value', {'x': '^1$'})))
        assert_that(solution.grade({"x": "1"}), is_(True))
        assert_that(solution.grade({"x": "2"}), is_(False))
        assert_that(solution.grade({"y": "1"}), is_(False))


class TestFreeResponsePart(AssessmentTestCase):

    def test_eq(self):
        part = parts.QFreeResponsePart()
        part2 = parts.QFreeResponsePart()

        assert_that(part, is_(part))
        assert_that(part, is_(part2))

        solution = solutions.QFreeResponseSolution(value=u"the value")

        part = parts.QFreeResponsePart(solutions=(solution,))
        assert_that(part, is_not(part2))

        part2 = parts.QFreeResponsePart(solutions=(solution,))
        assert_that(part, is_(part2))

        solution2 = solutions.QFreeResponseSolution(value=u"the value")
        part2 = parts.QFreeResponsePart(solutions=(solution2,))
        assert_that(part, is_(part2))

        solution2 = solutions.QFreeResponseSolution(value=u"not the value")
        part2 = parts.QFreeResponsePart(solutions=(solution2,))
        assert_that(part, is_not(part2))


class TestMathPart(AssessmentTestCase):

    def test_eq(self):
        solution = solutions.QMathSolution(solutions=[1, 2], 
                                           allowed_units=['times'])
        solution2 = solutions.QMathSolution(solutions=[3])
        part = parts.QMathPart(solutions=[solution, solution2])
        part2 = parts.QSymbolicMathPart()

        assert_that(part, is_(part))
        assert_that(part2, is_(part2))

        # subclasses would be equal to superclass, except for grader_interface
        assert_that(part, is_not(part2))
        part2.grader_interface = part.grader_interface
        # Except that the subclass implementation is always called??
        assert_that(part, is_not(part2))
        del part2.grader_interface
        assert_that(part2, is_not(part))

        assert_that(part, 
                    externalizes(has_entry('allowed_units', ['times'])))
        assert_that(part2, externalizes())


class TestFilePart(AssessmentTestCase):

    def test_allowed_mime(self):
        part = parts.QFilePart()

        def af(mt):
            assert_that(part.is_mime_type_allowed(mt), is_false())

        def at(mt):
            assert_that(part.is_mime_type_allowed(mt), is_true())

        # Bad input
        af(None)
        af('foobar')
        # no types
        af('text/plain')

        part.allowed_mime_types = (u'application/*', u'text/plain')
        assert_that(part, validly_provides(interfaces.IQFilePart))

        # exact match
        at('text/plain')
        # incomplete type
        af('text/*')
        # partial
        at('application/pdf')

        # wildcard
        part.allowed_mime_types = ('*/*',)
        at('audio/video')

    def test_allowed_extension(self):
        part = parts.QFilePart()

        def af(mt):
            assert_that(part.is_filename_allowed(mt), is_false())

        def at(mt):
            assert_that(part.is_filename_allowed(mt), is_true())

        # Bad input
        af(None)

        # No extensions defined is the same as wildcard
        at('noext')
        at('file.doc')

        part.allowed_extensions = (u'.doc',)
        at('file.DOC')
        at('file.doc')
        af('file.docx')

        part.allowed_extensions = (u'*',)
        at('file.doc')
        at('file.mp3')
        af(None)
