#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.cachedescriptors.property import readproperty

from zope.container.contained import Contained

from zope.location.interfaces import IContained
from zope.location.interfaces import ISublocations

from zope.mimetype.interfaces import IContentTypeAware

from persistent import Persistent

from nti.assessment import ASSESSMENT_INTERFACES

from nti.assessment.interfaces import PART_NTIID_TYPE

from nti.assessment.interfaces import IQPart
from nti.assessment.interfaces import IQAssessment
from nti.assessment.interfaces import IQSubmittable
from nti.assessment.interfaces import IQAssessedPart
from nti.assessment.interfaces import IQSubmittedPart
from nti.assessment.interfaces import IQPollSubmission
from nti.assessment.interfaces import IQNonGradablePart
from nti.assessment.interfaces import IQAssessedQuestion
from nti.assessment.interfaces import IQSurveySubmission
from nti.assessment.interfaces import IQuestionSubmission
from nti.assessment.interfaces import IQEditableEvaluation
from nti.assessment.interfaces import IQAssessedQuestionSet
from nti.assessment.interfaces import IQAssignmentSubmission
from nti.assessment.interfaces import IQuestionSetSubmission
from nti.assessment.interfaces import IQPartResponseNormalizer
from nti.assessment.interfaces import IQAssessmentJsonSchemaMaker
from nti.assessment.interfaces import IQLatexSymbolicMathSolution
from nti.assessment.interfaces import IQEvaluationContainerIdGetter

from nti.assessment.randomized.interfaces import IQuestionBank
from nti.assessment.randomized.interfaces import IQRandomizedPart
from nti.assessment.randomized.interfaces import IRandomizedQuestionSet
from nti.assessment.randomized.interfaces import IRandomizedPartsContainer

from nti.base.interfaces import IFile

from nti.coremetadata.mixins import VersionedMixin

from nti.coremetadata.utils import make_schema

from nti.coremetadata.interfaces import SYSTEM_USER_ID

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.dublincore.time_mixins import CreatedAndModifiedTimeMixin

from nti.externalization.oids import to_external_oid

from nti.externalization.representation import WithRepr

from nti.ntiids.ntiids import get_parts
from nti.ntiids.ntiids import make_ntiid
from nti.ntiids.ntiids import make_specific_safe

from nti.property.property import alias

from nti.publishing.mixins import CalendarPublishableMixin

from nti.recorder.mixins import RecordableMixin

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.interfaces import find_most_derived_interface

logger = __import__('logging').getLogger(__name__)


# functions


def grade_one_response(questionResponse, possible_answers):
    """
    :param questionResponse: The string to evaluate. It may be in latex notation
            or openmath XML notation, or plain text. We may edit the response
            to get something parseable.
    :param list possible_answers: A sequence of possible answers to compare
            `questionResponse` with.
    """

    match = False
    answers = [IQLatexSymbolicMathSolution(t) for t in possible_answers]
    for answer in answers:
        match = answer.grade(questionResponse)
        if match:
            return match
    return False


def assess(quiz, responses):
    result = {}
    for questionId, questionResponse in responses.iteritems():
        answers = quiz[questionId].answers
        result[questionId] = grade_one_response(questionResponse, answers)
    return result


def grader_for_solution_and_response(part, solution, response, creator=None):
    result = None
    if      (part.randomized or IQRandomizedPart.providedBy(part)) \
        and part.randomized_grader_interface:
        grader_interface = part.randomized_grader_interface

        # Only randomized graders care about creators; do this here so
        # we do not accidentally get randomized graders unintentionally.
        result = component.queryMultiAdapter((part, solution, response, creator),
                                             grader_interface,
                                             name=part.grader_name)
    else:
        grader_interface = part.grader_interface

    if result is None:
        result = component.queryMultiAdapter((part, solution, response),
                                             grader_interface,
                                             name=part.grader_name)
    return result
grader = grader_for_solution_and_response  # alias BWC


def grader_for_response(part, response):
    for solution in part.solutions or ():
        grader = grader_for_solution_and_response(part, solution, response)
        if grader is not None:
            return grader
    return None


def normalize_response(part, response):
    normalizer = component.queryMultiAdapter((part, response),
                                             IQPartResponseNormalizer)
    result = normalizer()
    return result


def interface_of_assessment(thing):
    for provided in ASSESSMENT_INTERFACES:
        if provided.providedBy(thing):
            return provided
    for provided in (IQPart, IQNonGradablePart):
        if provided.providedBy(thing):
            return provided
    return None
iface_of_assessment = interface_of_assessment


def get_containerId(item):
    getter = component.queryUtility(IQEvaluationContainerIdGetter)
    if getter is not None:
        result = getter(item)
    else:
        for name in ('__home__', '__parent__'):
            attribute = getattr(item, name, None)
            result = getattr(attribute, 'ntiid', None)
            if result:
                break
    return result


def compute_part_ntiid(part):
    parent = part.__parent__
    parent_parts = getattr(parent, 'parts', ())
    base_ntiid = getattr(parent, 'ntiid', None)
    if base_ntiid and parent_parts:
        # Gather all child parts ntiids.
        parent_part_ids = set()
        for child_part in parent_parts or ():
            child_part_ntiid = child_part.__dict__.get('ntiid')
            parent_part_ids.add(child_part_ntiid)
        parent_part_ids.discard(None)

        # Get initial part unique id
        uid = None
        if IQEditableEvaluation.providedBy(parent):
            uid = to_external_oid(part)
        uid = make_specific_safe(uid or str(0))  # legacy
        parts = get_parts(base_ntiid)

        idx = 0
        # Iterate until we find an ntiid that does not collide.
        while True:
            specific = "%s.%s" % (parts.specific, uid)
            result = make_ntiid(parts.date,
                                parts.provider,
                                PART_NTIID_TYPE,
                                specific)
            if result not in parent_part_ids:
                break
            idx += 1
            uid = idx
        return result
    return None


def is_randomized_question_set(question_set):
    """
    Determines whether the question set has questions in a
    random order.
    """
    return not IQuestionBank.providedBy(question_set) \
           and IRandomizedQuestionSet.providedBy(question_set)


def is_randomized_parts_container(assessment):
    """
    Determines whether the question set has questions in a
    random order. Currently only applicable on an IQuestionSet.
    """
    return IRandomizedPartsContainer.providedBy(assessment)


def is_part_auto_gradable(part):
    # Validate every part has grader.
    result = getattr(part, 'grader_interface', None) \
          or getattr(part, 'grader_name', None)
    return bool(result) and bool(part.solutions)


def can_be_auto_graded(assignment):
    for part in assignment.parts or ():
        question_set = part.question_set
        for question in question_set.questions or ():
            for part in question.parts or ():
                if not is_part_auto_gradable(part):
                    return False
    return True


def has_submitted_file(context):
    if     IQSurveySubmission.providedBy(context) \
        or IQAssessedQuestionSet.providedBy(context) \
        or IQuestionSetSubmission.providedBy(context):
        for question in context.questions or ():
            if has_submitted_file(question):
                return True
    elif   IQPollSubmission.providedBy(context) \
        or IQAssessedQuestion.providedBy(context) \
        or IQuestionSubmission.providedBy(context) \
        or IQAssignmentSubmission.providedBy(context):
        for part in context.parts or ():
            if has_submitted_file(part):
                return True
    elif IQAssessedPart.providedBy(context):
        return IFile.providedBy(context.submittedResponse)
    return IFile.providedBy(context)


# classes


@WithRepr
@interface.implementer(IContained,
                       IQSubmittable,
                       IContentTypeAware,
                       IAttributeAnnotatable)
class QSubmittable(SchemaConfigured,
                   VersionedMixin,
                   RecordableMixin,
                   CalendarPublishableMixin,
                   CreatedAndModifiedTimeMixin):

    available_for_submission_ending = \
        AdaptingFieldProperty(IQSubmittable['available_for_submission_ending'])

    available_for_submission_beginning = \
        AdaptingFieldProperty(IQSubmittable['available_for_submission_beginning'])

    not_after = alias('available_for_submission_ending')
    not_before = alias('available_for_submission_beginning')

    parameters = {}  # IContentTypeAware

    __parent__ = None

    def __init__(self, *args, **kwargs):
        SchemaConfigured.__init__(self, *args, **kwargs)

    @readproperty
    def __name__(self):
        return self.ntiid

    @readproperty
    def __home__(self):
        return self.__parent__


class QPersistentSubmittable(QSubmittable,
                             PersistentCreatedModDateTrackingObject):

    createdTime = 0
    creator = SYSTEM_USER_ID

    def __init__(self, *args, **kwargs):
        # schema configured is not cooperative
        QSubmittable.__init__(self, *args, **kwargs)
        PersistentCreatedModDateTrackingObject.__init__(self)


@WithRepr
@EqHash('submittedResponse', superhash=True)
@interface.implementer(IQSubmittedPart, ISublocations)
class QSubmittedPart(SchemaConfigured, Persistent, Contained):

    submittedResponse = None

    __external_can_create__ = False

    createDirectFieldProperties(IQSubmittedPart)

    def sublocations(self):
        part = self.submittedResponse
        if hasattr(part, '__parent__'):  # take ownership
            if part.__parent__ is None:
                part.__parent__ = self
            if part.__parent__ is self:
                yield part


# schema


class EvaluationSchemaMixin(object):
    """
    Mixin to pull a schema for a given implementation.
    """

    def schema(self, unused_user=None):
        schema = find_most_derived_interface(self, IQAssessment)
        result = make_schema(schema=schema,
                             user=None,
                             name='default',  # in case not in schema
                             maker=IQAssessmentJsonSchemaMaker)
        return result
AssessmentSchemaMixin = EvaluationSchemaMixin
