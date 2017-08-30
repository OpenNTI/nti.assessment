#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Having to do with submitting external data for grading.

.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time

from zope import component
from zope import interface

from zope.location.interfaces import ISublocations

from persistent import Persistent

from persistent.list import PersistentList

from nti.assessment._util import CreatorMixin
from nti.assessment._util import make_sublocations as _make_sublocations
from nti.assessment._util import dctimes_property_fallback as _dctimes_property_fallback

from nti.assessment.common import QSubmittedPart

from nti.assessment.interfaces import IQuestion
from nti.assessment.interfaces import IQuestionSet
from nti.assessment.interfaces import IQAssessedPart
from nti.assessment.interfaces import IQAssessedQuestion
from nti.assessment.interfaces import IQuestionSubmission
from nti.assessment.interfaces import IQAssessedQuestionSet

from nti.assessment.randomized.interfaces import IQRandomizedPart
from nti.assessment.randomized.interfaces import IRandomizedPartsContainer

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.coremetadata.mixins import ContainedMixin

from nti.externalization.representation import WithRepr

from nti.schema.eqhash import EqHash

from nti.schema.field import InvalidValue
from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import createDirectFieldProperties


@WithRepr
@interface.implementer(IQAssessedPart, ISublocations)
@EqHash('assessedValue', 'submittedResponse', superhash=True)
class QAssessedPart(QSubmittedPart, CreatorMixin):
    createDirectFieldProperties(IQAssessedPart)


@WithRepr
@interface.implementer(IQAssessedQuestion,
                       ICreated,
                       ILastModified,
                       ISublocations)
@EqHash('questionId', 'parts', superhash=True)
class QAssessedQuestion(SchemaConfigured,
                        ContainedMixin,
                        CreatorMixin,
                        Persistent):
    createDirectFieldProperties(IQAssessedQuestion)

    __external_can_create__ = False

    creator = None
    createdTime = _dctimes_property_fallback('createdTime', 'Date.Modified')
    lastModified = _dctimes_property_fallback('lastModified', 'Date.Created')

    def __init__(self, *args, **kwargs):
        super(QAssessedQuestion, self).__init__(*args, **kwargs)
        self.lastModified = self.createdTime = time.time()

    def updateLastMod(self, t=None):
        self.lastModified = (
            t if t is not None and t > self.lastModified else time.time()
        )
        return self.lastModified

    sublocations = _make_sublocations()


@WithRepr
@interface.implementer(IQAssessedQuestionSet,
                       ICreated,
                       ILastModified)
@EqHash('questionSetId', 'questions', superhash=True)
class QAssessedQuestionSet(SchemaConfigured,
                           ContainedMixin,
                           CreatorMixin,
                           Persistent):

    createDirectFieldProperties(IQAssessedQuestionSet)
    __external_can_create__ = False

    creator = None
    createdTime = _dctimes_property_fallback('createdTime', 'Date.Modified')
    lastModified = _dctimes_property_fallback('lastModified', 'Date.Created')

    def __init__(self, *args, **kwargs):
        super(QAssessedQuestionSet, self).__init__(*args, **kwargs)
        self.lastModified = self.createdTime = time.time()

    def updateLastMod(self, t=None):
        self.lastModified = (t if t is not None and t >
                             self.lastModified else time.time())
        return self.lastModified

    sublocations = _make_sublocations('questions')


def assess_question_submission(submission, registry=component):
    """
    Assess the given question submission.

    :return: An :class:`.interfaces.IQAssessedQuestion`.
    :param submission: An :class:`.interfaces.IQuestionSubmission`.
            The ``parts`` of this submission must be the same length
            as the parts of the question being submitted. If there is no
            answer to a part, then the corresponding value in the submission
            array should be ``None`` and the auto-assessment will be 0.0.
            (In the future, if we have questions
            with required and/or optional parts, we would implement that check
            here).
    :param registry: If given, an :class:`.IComponents`. If
            not given, the current component registry will be used.
            Used to look up the question set and question by id.
    :raises LookupError: If no question can be found for the submission.
    :raises Invalid: If a submitted part has the wrong kind of input
            to be graded.
    """

    question = registry.getUtility(IQuestion, name=submission.questionId)
    if len(question.parts) != len(submission.parts):
        raise ValueError(
            "Question (%s) and submission (%s) have different numbers of parts." %
            (len(question.parts), len(submission.parts)))

    creator = getattr(submission, 'creator', None)
    assessed_parts = PersistentList()

    for sub_part, q_part in zip(submission.parts, question.parts):
        # Grade what they submitted, if they submitted something. If they didn't
        # submit anything, it's automatically "wrong."
        try:
            if sub_part is not None:
                grade = q_part.grade(sub_part, creator)
            else:
                grade = 0.0
        except (LookupError, ValueError):
            # We couldn't grade the part because the submission was in the wrong
            # format. Translate this error to something more useful.
            __traceback_info__ = sub_part, q_part
            raise InvalidValue(
                value=sub_part, field=IQuestionSubmission['parts'])
        else:
            apart = QAssessedPart(submittedResponse=sub_part,
                                  assessedValue=grade)
            assessed_parts.append(apart)

    result = QAssessedQuestion(questionId=submission.questionId,
                               parts=assessed_parts)
    return result


def _do_assess_question_set_submission(question_set, set_submission, registry):
    questions_ntiids = {q.ntiid for q in question_set.Items}

    # NOTE: At this point we need to decide what to do for missing values
    # We are currently not really grading them at all, which is what we
    # did for the old legacy quiz stuff

    assessed = PersistentList()
    for sub_question in set_submission.questions:
        question = registry.getUtility(IQuestion,
                                       name=sub_question.questionId)

        ntiid = getattr(question, 'ntiid', None)
        if     ntiid in questions_ntiids \
            or question in question_set.Items:
            # Raises ComponentLookupError
            sub_assessed = IQAssessedQuestion(sub_question)
            assessed.append(sub_assessed)
        else:  # pragma: no cover
            logger.warn("Bad input, question (%s) not in question set (%s) (known: %s)",
                        question, question_set, questions_ntiids)

    # NOTE: We're not really creating some sort of aggregate grade here
    result = QAssessedQuestionSet(questionSetId=set_submission.questionSetId,
                                  questions=assessed)
    return result


def assess_question_set_submission(set_submission, registry=component):
    """
    Assess the given question set submission.

    :return: An :class:`.interfaces.IQAssessedQuestionSet`.
    :param set_submission: An :class:`.interfaces.IQuestionSetSubmission`.
    :param registry: If given, an :class:`.IComponents`. If
            not given, the current component registry will be used.
            Used to look up the question set and question by id.
    :raises LookupError: If no question can be found for the submission.
    """
    question_set = registry.getUtility(IQuestionSet,
                                       name=set_submission.questionSetId)
    # For marked randomized parts question sets, mark all parts
    # randomized and then undo post assessment.
    if IRandomizedPartsContainer.providedBy(question_set):
        try:
            for question in question_set.Items:
                for part in question.parts or ():
                    interface.alsoProvides(part, IQRandomizedPart)
            result = _do_assess_question_set_submission(question_set,
                                                        set_submission,
                                                        registry)
        finally:
            for question in question_set.Items:
                for part in question.parts or ():
                    try:
                        interface.noLongerProvides(part, IQRandomizedPart)
                    except ValueError:
                        # Concrete randomized type already.
                        pass
    else:
        result = _do_assess_question_set_submission(question_set,
                                                    set_submission,
                                                    registry)
    return result
