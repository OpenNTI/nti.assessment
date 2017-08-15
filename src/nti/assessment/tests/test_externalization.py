#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_not
from hamcrest import all_of
from hamcrest import has_key
from hamcrest import has_item
from hamcrest import equal_to
from hamcrest import not_none
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import has_entries
from hamcrest import assert_that
from hamcrest import has_property
from hamcrest import contains_string
does_not = is_not

from nti.testing.matchers import verifiably_provides

import os
import json

import fudge

from copy import deepcopy

from nti.assessment.interfaces import IQuestionSet
from nti.assessment.interfaces import IQPartSolutionsExternalizer

from nti.assessment.randomized.interfaces import IQuestionBank
from nti.assessment.randomized.interfaces import IQuestionIndexRange

from nti.externalization import internalization

from nti.externalization.externalization import to_external_object

from nti.externalization.tests import externalizes

from nti.assessment.tests import AssessmentTestCase

GIF_DATAURL = 'data:image/gif;base64,R0lGODlhCwALAIAAAAAA3pn/ZiH5BAEAAAEALAAAAAALAAsAAAIUhA+hkcuO4lmNVindo7qyrIXiGBYAOw=='


class TestExternalization(AssessmentTestCase):

    def test_file_upload(self):
        ext_obj = {
            'MimeType': 'application/vnd.nextthought.assessment.uploadedfile',
            'value': GIF_DATAURL,
            'filename': u'ichigo.gif',
        }

        assert_that(internalization.find_factory_for(ext_obj),
                    is_(not_none()))

        internal = internalization.find_factory_for(ext_obj)()
        internalization.update_from_external_object(internal,
                                                    ext_obj,
                                                    require_updater=True)

        # value changed to URI
        assert_that(ext_obj, does_not(has_key('value')))
        assert_that(ext_obj, has_key('url'))

        # We produced an image file, not a plain file
        assert_that(internal.getImageSize(), is_((11, 11)))

        # with the right content time and filename
        assert_that(internal, has_property('contentType', 'image/gif'))
        assert_that(internal, has_property('filename', 'ichigo.gif'))
        assert_that(internal, has_property('name', 'ichigo.gif'))

        assert_that(internal, externalizes(all_of(has_key('FileMimeType'),
                                                  has_key('filename'),
                                                  has_key('name'))))
        # But we have no URL because we're not in a connection anywhere

    def test_file_upload_2(self):
        # Temporary workaround for iPad bug.
        ext_obj = {
            'MimeType': 'application/vnd.nextthought.assessment.quploadedfile',
            'value': GIF_DATAURL,
            'filename': u'ichigo.gif',
            'name': u'ichigo'
        }

        assert_that(internalization.find_factory_for(ext_obj),
                    is_(not_none()))

        internal = internalization.find_factory_for(ext_obj)()
        internalization.update_from_external_object(internal,
                                                    ext_obj,
                                                    require_updater=True)

        # value changed to URI
        assert_that(ext_obj, does_not(has_key('value')))
        assert_that(ext_obj, has_key('url'))

        # We produced an image file, not a plain file
        assert_that(internal.getImageSize(), is_((11, 11)))

        # with the right content time and filename
        assert_that(internal, has_property('contentType', 'image/gif'))
        assert_that(internal, has_property('filename', 'ichigo.gif'))
        assert_that(internal, has_property('name', 'ichigo'))

        assert_that(internal, externalizes(all_of(has_key('FileMimeType'),
                                                  has_key('filename'),
                                                  has_key('name'))))
        # But we have no URL because we're not in a connection anywhere

    def test_modeled_response_uploaded(self):
        ext_obj = {
            'MimeType': 'application/vnd.nextthought.assessment.modeledcontentresponse',
            'value': [u'a part'],
        }

        assert_that(internalization.find_factory_for(ext_obj),
                    is_(not_none()))

        internal = internalization.find_factory_for(ext_obj)()
        internalization.update_from_external_object(internal,
                                                    ext_obj,
                                                    require_updater=True)

        assert_that(internal, has_property('value', is_(('a part',))))

    def test_wordbankentry(self):
        ext_obj = {
            'Class': 'WordEntry',
            'MimeType': 'application/vnd.nextthought.naqwordentry',
            'lang': u'en',
            'wid': u'14',
            'word': u'at',
        }

        assert_that(internalization.find_factory_for(ext_obj),
                    is_(not_none()))

        internal = internalization.find_factory_for(ext_obj)()
        internalization.update_from_external_object(internal,
                                                    ext_obj,
                                                    require_updater=True)

        assert_that(internal, has_property('word', is_('at')))
        assert_that(internal, has_property('wid', is_('14')))
        assert_that(internal, has_property('lang', is_('en')))
        assert_that(internal, has_property('content', is_('at')))

    def test_wordbank(self):
        ext_obj = {
            'Class': 'WordBank',
            'MimeType': 'application/vnd.nextthought.naqwordbank',
            'entries': [
                {
                    'Class': 'WordEntry',
                    'MimeType': 'application/vnd.nextthought.naqwordentry',
                    'lang': u'en',
                    'wid': u'14',
                    'word': u'at'
                }
            ],
            'unique': False
        }

        assert_that(internalization.find_factory_for(ext_obj),
                    is_(not_none()))

        internal = internalization.find_factory_for(ext_obj)()
        internalization.update_from_external_object(internal,
                                                    ext_obj,
                                                    require_updater=True)

        assert_that(internal, has_length(1))
        assert_that(internal, has_property('unique', is_(False)))

        word = internal.get('14')
        assert_that(word, has_property('content', 'at'))

    def test_question(self):
        ext_obj = {
            'Class': 'Question',
            "MimeType": "application/vnd.nextthought.naquestionfillintheblankwordbank",
            'parts': [
                {
                    "Class": "FillInTheBlankWithWordBankPart",
                    "MimeType": "application/vnd.nextthought.assessment.fillintheblankwithwordbankpart",
                    "content": u"",
                    "explanation": u"",
                    "hints": [],
                    "input": u"Step 1 <input type=\"blankfield\" name=\"001\" /><br />Step 2 <input type=\"blankfield\" name=\"002\" /><br />Step 3 <input type=\"blankfield\" name=\"003\" /><br />Step 4 <input type=\"blankfield\" name=\"004\" /><br />",
                    "randomized": False
                },
            ],
            "wordbank": {
                "Class": "WordBank",
                "MimeType": "application/vnd.nextthought.naqwordbank",
                'entries': [
                    {
                        'Class': 'WordEntry',
                        'MimeType': 'application/vnd.nextthought.naqwordentry',
                        'wid': u'14',
                        'word': u'at'
                    }
                 ]
            }
        }

        assert_that(internalization.find_factory_for(ext_obj),
                    is_(not_none()))

        internal = internalization.find_factory_for(ext_obj)()
        internalization.update_from_external_object(internal,
                                                    ext_obj,
                                                    require_updater=True)

        part = internal.parts[0]
        assert_that(part, has_property('input', contains_string('<input')))
        assert_that(internal,
                    externalizes(all_of(has_entry('Class', 'Question')))),

    def test_regex(self):
        ext_obj = {
            'MimeType': 'application/vnd.nextthought.naqregex',
            'pattern': u"(^yes\\s*[,|\\s]\\s*I will(\\.)?$)|(^no\\s*[,|\\s]\\s*I (won't|will not)(\\.)?$)",
            'Class': 'RegEx',
            'solution': u'yes, I will'
        }
        assert_that(internalization.find_factory_for(ext_obj),
                    is_(not_none()))

        internal = internalization.find_factory_for(ext_obj)()
        internalization.update_from_external_object(internal,
                                                    ext_obj,
                                                    require_updater=True)

        assert_that(internal,
                    has_property('solution', is_(u'yes, I will')))
        assert_that(internal,
                    has_property('pattern',
                                 is_(u"(^yes\\s*[,|\\s]\\s*I will(\\.)?$)|(^no\\s*[,|\\s]\\s*I (won't|will not)(\\.)?$)")))

    def test_regex_part(self):
        ext_obj = {
            'MimeType': 'application/vnd.nextthought.assessment.fillintheblankshortanswerpart',
            'explanation': u'',
            'content': u'Will you visit America next year?',
            'weight': .5,
            'solutions': [
                {
                    'MimeType': 'application/vnd.nextthought.assessment.fillintheblankshortanswersolution',
                    'value': {
                        u'001': {
                            'MimeType': u'application/vnd.nextthought.naqregex',
                            'pattern': u"(^yes\\s*[,|\\s]\\s*I will(\\.)?$)|(^no\\s*[,|\\s]\\s*I (won't|will not)(\\.)?$)",
                            'Class': 'RegEx',
                            'solution': u'yes, I will'
                        }
                    },
                    'Class': 'FillInTheBlankShortAnswerSolution',
                    'weight': 1.0}
            ],
            'Class': 'FillInTheBlankShortAnswerPart',
            'hints': []
        }
        missing_classes_ext = deepcopy(ext_obj)
        solution_ext = missing_classes_ext.get('solutions')[0]
        solution_ext.pop('Class', None)
        missing_classes_ext.pop('Class', None)

        assert_that(internalization.find_factory_for(ext_obj),
                    is_(not_none()))

        internal = internalization.find_factory_for(ext_obj)()
        internalization.update_from_external_object(internal, ext_obj,
                                                    require_updater=True)
        hash(internal)

        assert_that(internal, has_property('solutions', has_length(1)))
        assert_that(internal, has_property('weight', is_(.5)))
        sol = internal.solutions[0]
        assert_that(sol,
                    has_property('value',
                                 has_entry('001', has_property('solution', 'yes, I will'))))

        # Validate we can internalize without class
        internal = internalization.find_factory_for(missing_classes_ext)()
        internalization.update_from_external_object(internal,
                                                    missing_classes_ext,
                                                    require_updater=True)

    def test_question_set(self):
        path = os.path.join(os.path.dirname(__file__), "questionset.json")
        with open(path, "r") as fp:
            ext_obj = json.load(fp)

        factory = internalization.find_factory_for(ext_obj)
        assert_that(factory, is_(not_none()))

        internal = factory()
        internalization.update_from_external_object(internal, ext_obj,
                                                    require_updater=True)

        ntiid = u"tag:nextthought.com,2011-10:OU-NAQ-BIOL2124_F_2014_Human_Physiology.naq.set.qset:intro_quiz1"
        internal.ntiid = ntiid

        assert_that(internal, verifiably_provides(IQuestionSet))
        assert_that(internal, has_property('questions', has_length(20)))

        assert_that(list(internal.Items), has_length(20))

        assert_that(internal,
                    externalizes(all_of(has_entry('NTIID', is_(ntiid)),
                                        has_entry('Class', is_('QuestionSet')),
                                        has_entry('MimeType', is_('application/vnd.nextthought.naquestionset')),
                                        has_entry('questions', has_length(20)))))

        exported = to_external_object(internal, name="exporter")
        assert_that(exported, has_entries('NTIID', ntiid,
                                          'Class', 'QuestionSet',
                                          'MimeType', 'application/vnd.nextthought.naquestionset',
                                          'questions', has_length(20)))

    def test_question_set_summary(self):
        path = os.path.join(os.path.dirname(__file__), "questionset.json")
        with open(path, "r") as fp:
            ext_obj = json.load(fp)

        factory = internalization.find_factory_for(ext_obj)
        assert_that(factory, is_(not_none()))

        internal = factory()
        internalization.update_from_external_object(internal, ext_obj,
                                                    require_updater=True)

        ntiid = u"tag:nextthought.com,2011-10:OU-NAQ-BIOL2124_F_2014_Human_Physiology.naq.set.qset:intro_quiz1"
        internal.ntiid = ntiid

        assert_that(internal, verifiably_provides(IQuestionSet))
        assert_that(internal, has_property('questions', has_length(20)))

        assert_that(list(internal.Items), has_length(20))

        ext_obj = to_external_object(internal, name="summary")
        assert_that(ext_obj,
                    has_entries('NTIID', is_(ntiid),
                                'Class', is_('QuestionSet'),
                                'MimeType', is_('application/vnd.nextthought.naquestionset')))
        assert_that(ext_obj, does_not(has_item('questions')))

    @fudge.patch('nti.assessment.randomized.get_seed')
    def test_question_bank(self, mock_gs):

        mock_gs.is_callable().with_args().returns(None)

        path = os.path.join(os.path.dirname(__file__), "questionbank.json")
        with open(path, "r") as fp:
            ext_obj = json.load(fp)

        factory = internalization.find_factory_for(ext_obj)
        assert_that(factory, is_(not_none()))

        internal = factory()
        internalization.update_from_external_object(internal, ext_obj,
                                                    require_updater=True)

        ntiid = u"tag:nextthought.com,2011-10:OU-NAQ-BIOL2124_F_2014_Human_Physiology.naq.set.qset:intro_quiz1"
        internal.ntiid = ntiid

        assert_that(internal, verifiably_provides(IQuestionBank))

        assert_that(internal, has_property('draw', is_(5)))
        assert_that(internal, has_property('questions', has_length(20)))

        internal.draw = 2
        internal.ranges = [
            IQuestionIndexRange([0, 5]),
            IQuestionIndexRange([6, 10])
        ]

        assert_that(internal,
                    externalizes(all_of(has_entry('draw', is_(2)),
                                        has_entry('NTIID', is_(ntiid)),
                                        has_entry('Class', is_('QuestionSet')),
                                        has_entry('MimeType', is_('application/vnd.nextthought.naquestionbank')),
                                        has_entry('ranges', has_length(2)))))

        ext_obj = to_external_object(internal)
        assert_that(ext_obj, has_entry('questions', has_length(20)))
        rand_question = ext_obj['questions'][1]
        assert_that(rand_question, has_entry('parts', has_length(1)))
        assert_that(rand_question['parts'][0],
                    has_entry('randomized', is_(True)))
        assert_that(rand_question['parts'][0],
                    has_entry('MimeType', is_('application/vnd.nextthought.assessment.multiplechoicepart')))

    def test_assignment(self):
        path = os.path.join(
            os.path.dirname(__file__), "assignment_no_solutions.json")
        with open(path, "r") as fp:
            ext_obj = json.load(fp)
        factory = internalization.find_factory_for(ext_obj)
        assert_that(factory, is_(not_none()))
        internal = factory()
        internalization.update_from_external_object(internal, ext_obj,
                                                    require_updater=True)

    def test_discussion_assignment(self):
        discussion_ntiid = u'tag:nextthought.com,2015-11-30:DiscussionTest'
        ext_obj = {
            "CategoryName": u"homework",
            "Class": "DiscussionAssignment",
            "MimeType": u'application/vnd.nextthought.assessment.discussionassignment',
            "available_for_submission_beginning": u"2015-05-12T05:00:00Z",
            "available_for_submission_ending": u"2024-07-16T04:59:00Z",
            "content": u"This is a description of an <b>assignment.</b>",
            "is_non_public": False,
            "no_submit": True,
            "parts": [],
            "publishBeginning": None,
            "publishEnding": None,
            "discussion_ntiid": discussion_ntiid,
            "title": u"Test Discussion assignment"
        }
        factory = internalization.find_factory_for(ext_obj)
        assert_that(factory, is_(not_none()))
        internal = factory()
        internalization.update_from_external_object(internal, ext_obj,
                                                    require_updater=True)
        assert_that(internal.discussion_ntiid, is_(discussion_ntiid))

    def test_assignment_summary(self):
        path = os.path.join(
            os.path.dirname(__file__), "assignment_no_solutions.json")
        with open(path, "r") as fp:
            ext_obj = json.load(fp)
        factory = internalization.find_factory_for(ext_obj)
        assert_that(factory, is_(not_none()))
        internal = factory()
        internalization.update_from_external_object(
            internal, ext_obj, require_updater=True)

        ext_obj = to_external_object(internal, name="summary")
        parts_ext = ext_obj.get('parts')[0]
        assert_that(parts_ext,
                    has_entries('Class', is_('AssignmentPart'),
                                'MimeType', is_('application/vnd.nextthought.assessment.assignmentpart')))
        assert_that(parts_ext, does_not(has_item('question_set')))

    @fudge.patch('nti.assessment.randomized.get_seed')
    def test_solutions_externalizer(self, mock_gs):
        path = os.path.join(os.path.dirname(__file__), "questionset.json")
        with open(path, "r") as fp:
            ext_obj = json.load(fp)

        question_ext = ext_obj['questions'][0]
        factory = internalization.find_factory_for(question_ext)
        internal = factory()
        internalization.update_from_external_object(internal, question_ext)

        part = internal.parts[0]
        externalizer = IQPartSolutionsExternalizer(part)
        org_solutions = externalizer.to_external_object()

        mock_gs.is_callable().with_args().returns(100)
        part.randomized = True
        externalizer = IQPartSolutionsExternalizer(part)
        rand_solutions = externalizer.to_external_object()

        assert_that(org_solutions[0]['value'],
                    is_not(equal_to(rand_solutions[0]['value'])))

        part.randomized = False
        externalizer = IQPartSolutionsExternalizer(part)
        no_rand_solutions = externalizer.to_external_object()

        assert_that(org_solutions[0]['value'],
                    is_(equal_to(no_rand_solutions[0]['value'])))
