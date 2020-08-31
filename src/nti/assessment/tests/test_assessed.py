#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import raises
from hamcrest import calling
from hamcrest import contains
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import greater_than
from hamcrest import has_property

import fudge

from nti.testing.matchers import verifiably_provides

from zope import component
from zope import interface

from nti.assessment.assessed import QAssessedPart
from nti.assessment.assessed import QAssessedQuestion
from nti.assessment.assessed import QAssessedQuestionSet

from nti.assessment.common import has_submitted_file

from nti.assessment.interfaces import IQuestion
from nti.assessment.interfaces import IQuestionSet
from nti.assessment.interfaces import IQAssessedPart
from nti.assessment.interfaces import IQAssessedQuestion
from nti.assessment.interfaces import IQAssessedQuestionSet

from nti.assessment.parts import QFilePart
from nti.assessment.parts import QNumericMathPart
from nti.assessment.parts import QFreeResponsePart
from nti.assessment.parts import QModeledContentPart
from nti.assessment.parts import QMultipleChoicePart

from nti.assessment.question import QQuestion
from nti.assessment.question import QQuestionSet

from nti.assessment.randomized.interfaces import IRandomizedPartsContainer

from nti.assessment.response import QUploadedFile
from nti.assessment.response import QModeledContentResponse

from nti.assessment.solution import QNumericMathSolution
from nti.assessment.solution import QFreeResponseSolution
from nti.assessment.solution import QMultipleChoiceSolution

from nti.assessment.submission import QuestionSubmission
from nti.assessment.submission import QuestionSetSubmission

from nti.base.interfaces import DEFAULT_CONTENT_TYPE

from nti.base.interfaces import ILastModified

from nti.externalization.externalization import toExternalObject

from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

from nti.schema.interfaces import InvalidValue

from nti.assessment.tests import lineage
from nti.assessment.tests import AssessmentTestCase
from nti.assessment.tests import check_old_dublin_core as _check_old_dublin_core

from nti.externalization.tests import externalizes


class TestAssessedPart(AssessmentTestCase):

    def test_externalizes(self):
        assert_that(QAssessedPart(),
                    verifiably_provides(IQAssessedPart))
        assert_that(QAssessedPart(),
                    externalizes(has_entry('Class', 'AssessedPart')))
        assert_that(find_factory_for(toExternalObject(QAssessedPart())),
                    is_(none()))

        # These cannot be created externally, so we're not worried about
        # what happens when they are updated...this test just serves to document
        # the behaviour. In the past, updating from external objects transformed
        # the value into an IQResponse...but the actual assessment code itself assigned
        # the raw string/int value. Responses would be ideal, but that could break existing
        # client code. The two behaviours are now unified
        part = QAssessedPart()
        update_from_external_object(part, {"submittedResponse": u"The text response"},
                                    require_updater=True)

        assert_that(part.submittedResponse, is_("The text response"))

    def test_hash(self):
        part = QAssessedPart(submittedResponse=[1, 2, 3])
        hash(part)
        assert_that(part, is_(part))


class TestAssessedQuestion(AssessmentTestCase):

    def test_externalizes(self):
        assert_that(QAssessedQuestion(),
                    verifiably_provides(IQAssessedQuestion))
        assert_that(QAssessedQuestion(),
                    verifiably_provides(ILastModified))
        assert_that(QAssessedQuestion(),
                    externalizes(has_entry('Class', 'AssessedQuestion')))
        assert_that(find_factory_for(toExternalObject(QAssessedQuestion())),
                    is_(none()))

    def test_assess(self):
        part = QFreeResponsePart(solutions=(QFreeResponseSolution(value=u'correct'),))
        question = QQuestion(parts=(part,))
        assert_that(hash(question), is_(hash(question)))
        assert_that(question, is_(question))
        component.provideUtility(question, provides=IQuestion,
                                 name="1")

        sub = QuestionSubmission(questionId=u"1", parts=(u'correct',))

        result = IQAssessedQuestion(sub)
        assert_that(result, has_property('questionId', "1"))
        assert_that(result,
                    has_property('parts',
                                 contains(QAssessedPart(submittedResponse=u'correct',
                                                        assessedValue=1.0))))

        _check_old_dublin_core(result)

    def test_assess_with_null_part(self):
        # A null part means no answer was provided
        part = QFreeResponsePart(solutions=(QFreeResponseSolution(value=u'correct'),))
        question = QQuestion(parts=(part,))
        component.provideUtility(question, provides=IQuestion,
                                 name="1")

        sub = QuestionSubmission()
        update_from_external_object(sub, {'questionId': u"1", 'parts': [None]},
                                    notify=False)

        result = IQAssessedQuestion(sub)
        assert_that(result, has_property('questionId', "1"))
        assert_that(result,
                    has_property('parts',
                                 contains(QAssessedPart(submittedResponse=None,
                                                        assessedValue=0.0))))

        _check_old_dublin_core(result)

    def test_assess_with_incorrect_part(self):
        # An incorrect part raises a useful validation error
        part = QFreeResponsePart(solutions=(QFreeResponseSolution(value=u'correct'),))
        question = QQuestion(parts=(part,))
        component.provideUtility(question, provides=IQuestion,
                                 name="1")

        sub = QuestionSubmission()
        update_from_external_object(sub, {'questionId': u"1", 'parts': [[]]},
                                    notify=False)

        assert_that(calling(IQAssessedQuestion).with_args(sub),
                    raises(InvalidValue))

    def test_assess_with_incorrect_multichoice_part(self):
        part = QMultipleChoicePart(solutions=(QMultipleChoiceSolution(value=1),))
        question = QQuestion(parts=(part,))
        assert_that(hash(question), is_(hash(question)))
        assert_that(question, is_(question))

        component.provideUtility(question, provides=IQuestion,
                                 name="1")

        sub = QuestionSubmission()
        update_from_external_object(sub, {'questionId': u"1", 'parts': [u'']},
                                    notify=False)

        assert_that(calling(IQAssessedQuestion).with_args(sub),
                    raises(InvalidValue))

    def test_assess_with_incorrect_float_part(self):
        part = QNumericMathPart(solutions=(QNumericMathSolution(value=1),))
        question = QQuestion(parts=(part,))
        component.provideUtility(question, provides=IQuestion,
                                 name="1")

        sub = QuestionSubmission()
        update_from_external_object(sub, {'questionId': u"1", 'parts': [u'']},
                                    notify=False)

        assert_that(calling(IQAssessedQuestion).with_args(sub),
                    raises(InvalidValue))

    def test_assess_with_file_part(self):
        part = QFilePart()
        part.allowed_mime_types = ('*/*',)
        part.allowed_extensions = '*'
        question = QQuestion(parts=(part,))

        component.provideUtility(question, provides=IQuestion,
                                 name="1")

        sub = QuestionSubmission(questionId=u"1", parts=(u'correct',))
        # Wrong submission type, cannot be assessed at all
        assert_that(calling(IQAssessedQuestion).with_args(sub),
                    raises(TypeError))

        # Right submission type, but not a valid submission
        sub = QuestionSubmission(questionId=u"1",
                                 parts=(QUploadedFile(),))
        assert_that(calling(IQAssessedQuestion).with_args(sub),
                    raises(interface.Invalid))

        sub = QuestionSubmission(questionId=u"1",
                                 parts=(QUploadedFile(data=b'1234',
                                                      contentType='text/plain',
                                                      filename=u'foo.txt'),))
        assert_that(has_submitted_file(sub), is_(True))

        result = IQAssessedQuestion(sub)
        assert_that(has_submitted_file(result), is_(True))
        assert_that(result, has_property('questionId', "1"))
        assert_that(result,
                    has_property('parts',
                                 contains(QAssessedPart(submittedResponse=sub.parts[0],
                                                        assessedValue=None))))
        assert_that(sub.parts[0],
                    has_property('lastModified', greater_than(0)))
        assert_that(sub.parts[0], has_property('createdTime', greater_than(0)))

        # Now if the part gets constraints on filename or mimeType or size
        # submission can fail
        part.allowed_mime_types = (DEFAULT_CONTENT_TYPE,)
        assert_that(calling(IQAssessedQuestion).with_args(sub),
                    raises(interface.Invalid, 'mimeType'))

        part.allowed_mime_types = ('*/*',)
        part.allowed_extensions = ('.doc',)
        assert_that(calling(IQAssessedQuestion).with_args(sub),
                    raises(interface.Invalid, 'filename'))

        part.allowed_extensions = '*'
        part.max_file_size = 0
        assert_that(calling(IQAssessedQuestion).with_args(sub),
                    raises(interface.Invalid, 'max_file_size'))

    def test_assess_with_modeled_content_part(self):
        part = QModeledContentPart()
        question = QQuestion(parts=(part,))

        component.provideUtility(question, provides=IQuestion,
                                 name="1")

        sub = QuestionSubmission(questionId=u"1", parts=(u'correct',))
        # Wrong submission type, cannot be assessed at all
        assert_that(calling(IQAssessedQuestion).with_args(sub),
                    raises(TypeError))

        # Right submission type, but not a valid submission
        sub = QuestionSubmission(questionId=u"1",
                                 parts=(QModeledContentResponse(),))
        assert_that(calling(IQAssessedQuestion).with_args(sub),
                    raises(interface.Invalid))

        sub = QuestionSubmission(questionId=u"1",
                                 parts=(QModeledContentResponse(value=['a part']),))

        result = IQAssessedQuestion(sub)
        assert_that(result, has_property('questionId', "1"))
        assert_that(result,
                    has_property('parts',
                                 contains(QAssessedPart(submittedResponse=sub.parts[0],
                                                        assessedValue=None))))


class TestAssessedQuestionSet(AssessmentTestCase):

    def test_externalizes(self):
        assert_that(QAssessedQuestionSet(),
                    verifiably_provides(IQAssessedQuestionSet))
        assert_that(QAssessedQuestionSet(),
                    verifiably_provides(ILastModified))
        assert_that(QAssessedQuestionSet(),
                    externalizes(has_entries('Class', 'AssessedQuestionSet',
                                             'MimeType', 'application/vnd.nextthought.assessment.assessedquestionset')))
        assert_that(find_factory_for(toExternalObject(QAssessedQuestionSet())),
                    is_(none()))

    def test_assess(self):
        part = QFreeResponsePart(solutions=(QFreeResponseSolution(value=u'correct'),))
        question = QQuestion(parts=(part,))
        question_set = QQuestionSet(questions=(question,))

        component.provideUtility(question,
                                 provides=IQuestion,
                                 name="1")
        component.provideUtility(question_set,
                                 provides=IQuestionSet,
                                 name="2")

        sub = QuestionSubmission(questionId=u"1", parts=(u'correct',))
        set_sub = QuestionSetSubmission(questionSetId=u"2", questions=(sub,))

        result = IQAssessedQuestionSet(set_sub)
        assert_that(has_submitted_file(result), is_(False))
        assert_that(result, has_property('questionSetId', "2"))
        assert_that(result,
                    has_property('questions',
                                 contains(has_property('parts',
                                                       contains(QAssessedPart(submittedResponse=u'correct',
                                                                              assessedValue=1.0))))))
        # consistent hashing
        assert_that(hash(result), is_(hash(result)))

        for question in result.questions:
            parents = list(lineage(question))
            assert_that(parents, has_length(1))

        ext_obj = toExternalObject(result)
        assert_that(ext_obj, has_entry('questions', has_length(1)))

        _check_old_dublin_core(result)

        for question in result.questions:
            parents = list(lineage(question))
            assert_that(parents[-1], is_(result))
            assert_that(parents, has_length(greater_than(1)))
            for part in question.parts:
                parents = list(lineage(part))
                assert_that(parents, has_length(greater_than(2)))
                assert_that(parents[-1], is_(result))

    def test_assess_not_same_instance_question_but_id_matches(self):
        part = QFreeResponsePart(solutions=(QFreeResponseSolution(value=u'correct'),))
        question = QQuestion(parts=(part,))
        ntiid = u'tag:nextthought.com,2015-11-30:Test'
        question.ntiid = ntiid
        question_set = QQuestionSet(questions=(question,))

        component.provideUtility(question,
                                 provides=IQuestion,
                                 name=ntiid)
        component.provideUtility(question_set,
                                 provides=IQuestionSet,
                                 name="2")
        # New instance
        part = QFreeResponsePart(solutions=(QFreeResponseSolution(value=u'correct2'),))
        question = QQuestion(parts=(part,))
        question.ntiid = ntiid

        component.provideUtility(question,
                                 provides=IQuestion,
                                 name=ntiid)

        assert_that(question, is_not(question_set.questions[0]))

        sub = QuestionSubmission(questionId=ntiid, parts=(u'correct2',))
        set_sub = QuestionSetSubmission(questionSetId=u"2", questions=(sub,))

        result = IQAssessedQuestionSet(set_sub)
        assert_that(has_submitted_file(result), is_(False))
        assert_that(result, has_property('questionSetId', "2"))
        assert_that(result,
                    has_property('questions',
                                 contains(has_property('parts',
                                                       contains(QAssessedPart(submittedResponse=u'correct2',
                                                                              assessedValue=1.0))))))

        ext_obj = toExternalObject(result)
        assert_that(ext_obj, has_entry('questions', has_length(1)))

    def test_assess_not_same_instance_question_but_equals(self):
        part = QFreeResponsePart(solutions=(QFreeResponseSolution(value=u'correct'),))
        question = QQuestion(content=u'foo', parts=(part,))
        question_set = QQuestionSet(questions=(question,))

        # New instance
        part = QFreeResponsePart(solutions=(QFreeResponseSolution(value=u'correct'),))
        question = QQuestion(content=u'foo', parts=(part,))

        hash(question_set)

        component.provideUtility(question,
                                 provides=IQuestion,
                                 name="abc")
        component.provideUtility(question_set,
                                 provides=IQuestionSet,
                                 name="2")

        sub = QuestionSubmission(questionId=u'abc', parts=(u'correct',))
        set_sub = QuestionSetSubmission(questionSetId=u"2", questions=(sub,))

        result = IQAssessedQuestionSet(set_sub)
        assert_that(has_submitted_file(result), is_(False))
        assert_that(result, has_property('questionSetId', "2"))
        assert_that(result,
                    has_property('questions',
                                 contains(has_property('parts',
                                                       contains(QAssessedPart(submittedResponse=u'correct',
                                                                              assessedValue=1.0))))))

        ext_obj = toExternalObject(result)
        assert_that(ext_obj, has_entry('questions', has_length(1)))

    @fudge.patch("nti.assessment.randomized.get_seed")
    def test_assess_randomized_proxy(self, mock_get_seed):
        """
        With a marked randomized-parts question set, validate assessment.
        """
        mock_get_seed.is_callable().returns('34870983478047803')
        solution = QMultipleChoiceSolution(1)
        choices = (u"A", u"B", u"C", u"D", u"E", u"F")
        part = QMultipleChoicePart(solutions=(solution,),
                                   choices=list(choices))
        question = QQuestion(parts=(part,))
        ntiid = u'tag:nextthought.com,2015-11-30:Test_Rand_Proxy'
        question.ntiid = ntiid
        question_set = QQuestionSet(questions=(question,))
        interface.alsoProvides(question_set, IRandomizedPartsContainer)

        component.provideUtility(question,
                                 provides=IQuestion,
                                 name=ntiid)
        component.provideUtility(question_set,
                                 provides=IQuestionSet,
                                 name="2")

        # Incorrect
        sub = QuestionSubmission(questionId=ntiid, parts=(1,))
        set_sub = QuestionSetSubmission(questionSetId=u"2", questions=(sub,))
        result = IQAssessedQuestionSet(set_sub)
        assert_that(result, has_property('questionSetId', "2"))
        assert_that(result,
                    has_property('questions',
                                 contains(has_property('parts',
                                                       contains(QAssessedPart(submittedResponse=1,
                                                                              assessedValue=0.0))))))

        # `B` is index 5 with this seed
        sub.parts = (5,)
        result = IQAssessedQuestionSet(set_sub)
        assert_that(result, has_property('questionSetId', "2"))
        assert_that(result,
                    has_property('questions',
                                 contains(has_property('parts',
                                                       contains(QAssessedPart(submittedResponse=5,
                                                                              assessedValue=1.0))))))
