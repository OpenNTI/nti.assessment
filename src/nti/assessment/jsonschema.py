#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.assessment import FIELDS
from nti.assessment import ACCEPTS

from nti.assessment.common import make_schema

from nti.assessment.interfaces import IQPart
from nti.assessment.interfaces import IQPoll
from nti.assessment.interfaces import IQSurvey
from nti.assessment.interfaces import IQuestion
from nti.assessment.interfaces import IQFilePart
from nti.assessment.interfaces import IQuestionSet
from nti.assessment.interfaces import IQAssignment
from nti.assessment.interfaces import IQAssessment
from nti.assessment.interfaces import IQOrderingPart
from nti.assessment.interfaces import IQMatchingPart
from nti.assessment.interfaces import IQConnectingPart
from nti.assessment.interfaces import IQAssignmentPart
from nti.assessment.interfaces import IQFreeResponsePart
from nti.assessment.interfaces import IQMultipleChoicePart
from nti.assessment.interfaces import IQModeledContentPart
from nti.assessment.interfaces import IQEvaluationJsonSchemaMaker
from nti.assessment.interfaces import IQMultipleChoiceMultipleAnswerPart

from nti.coremetadata.jsonschema import CoreJsonSchemafier

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.recorder.interfaces import IRecordable
from nti.recorder.interfaces import IRecordableContainer

ITEMS = StandardExternalFields.ITEMS

logger = __import__('logging').getLogger(__name__)


class BaseJsonSchemafier(CoreJsonSchemafier):

    IGNORE_INTERFACES = CoreJsonSchemafier.IGNORE_INTERFACES + \
                        (IRecordable, IRecordableContainer)


@interface.implementer(IQEvaluationJsonSchemaMaker)
class EvaluationJsonSchemaMaker(object):

    maker = BaseJsonSchemafier

    def make_schema(self, schema=IQAssessment, unused_user=None):
        result = LocatedExternalDict()
        maker = self.maker(schema)
        result[FIELDS] = maker.make_schema()
        return result
AssessmentJsonSchemaMaker = EvaluationJsonSchemaMaker


@interface.implementer(IQEvaluationJsonSchemaMaker)
class ItemContainerJsonSchemaMaker(EvaluationJsonSchemaMaker):

    has_items = True
    ref_interfaces = ()
    full_ref_schema = False

    def make_schema(self, schema=IQAssessment, user=None):
        result = super(ItemContainerJsonSchemaMaker, self).make_schema(schema, user)
        accepts = result[ACCEPTS] = {}
        for iface in self.ref_interfaces:
            mimeType = iface.getTaggedValue('_ext_mime_type')
            if self.full_ref_schema:
                accepts[mimeType] = make_schema(schema=iface)
            else:
                accepts[mimeType] = make_schema(schema=iface).get(FIELDS)
        if self.has_items:
            fields = result[FIELDS]
            base_types = sorted(accepts.keys())
            if len(base_types) > 1:
                fields[ITEMS]['base_type'] = base_types
            else:
                fields[ITEMS]['base_type'] = base_types[0]
        return result


@interface.implementer(IQEvaluationJsonSchemaMaker)
class AssignmentJsonSchemaMaker(ItemContainerJsonSchemaMaker):

    has_items = False
    ref_interfaces = (IQAssignmentPart,)

    def make_schema(self, schema=IQAssignment, user=None):
        result = super(AssignmentJsonSchemaMaker, self).make_schema(schema, user)
        return result


@interface.implementer(IQEvaluationJsonSchemaMaker)
class AssignmentPartJsonSchemaMaker(ItemContainerJsonSchemaMaker):

    has_items = False
    ref_interfaces = (IQuestionSet,)

    def make_schema(self, schema=IQAssignmentPart, user=None):
        result = super(AssignmentPartJsonSchemaMaker, self).make_schema(schema, user)
        return result


@interface.implementer(IQEvaluationJsonSchemaMaker)
class QuestionSetJsonSchemaMaker(ItemContainerJsonSchemaMaker):

    has_items = False
    ref_interfaces = (IQuestion,)
    full_ref_schema = True

    def make_schema(self, schema=IQuestionSet, user=None):
        result = super(QuestionSetJsonSchemaMaker, self).make_schema(schema, user)
        return result


@interface.implementer(IQEvaluationJsonSchemaMaker)
class QuestionJsonSchemaMaker(ItemContainerJsonSchemaMaker):

    has_items = False

    # Warning!!! ... handling only a subset so far.
    ref_interfaces = (IQMatchingPart, IQMultipleChoicePart, IQOrderingPart,
                      IQMultipleChoiceMultipleAnswerPart, IQFreeResponsePart,
                      IQConnectingPart, IQFilePart, IQModeledContentPart)

    def make_schema(self, schema=IQuestion, user=None):
        result = super(QuestionJsonSchemaMaker, self).make_schema(schema, user)
        return result


class PartJsonSchemaMaker(ItemContainerJsonSchemaMaker):

    has_items = False

    ref_interfaces = ()

    def make_schema(self, schema=IQPart, user=None):
        result = super(PartJsonSchemaMaker, self).make_schema(schema, user)
        return result


@interface.implementer(IQEvaluationJsonSchemaMaker)
class PollJsonSchemaMaker(ItemContainerJsonSchemaMaker):

    has_items = False

    def make_schema(self, schema=IQPoll, user=None):
        result = super(PollJsonSchemaMaker, self).make_schema(schema, user)
        return result


@interface.implementer(IQEvaluationJsonSchemaMaker)
class SurveyJsonSchemaMaker(ItemContainerJsonSchemaMaker):

    has_items = False
    ref_interfaces = (IQPoll,)

    def make_schema(self, schema=IQSurvey, user=None):
        result = super(SurveyJsonSchemaMaker, self).make_schema(schema, user)
        return result
