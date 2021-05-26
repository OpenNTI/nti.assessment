#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

try:
    from collections.abc import Sequence
except ImportError: # pragma: no cover
    # Python 2
    from collections import Sequence

import six
from collections import Mapping

from zope import component
from zope import interface

from zope.proxy.decorator import SpecificationDecoratorBase

from nti.assessment._hooks import ntiid_object_hook

import nti.assessment.interfaces as assessment_interfaces

from nti.assessment.interfaces import IAvoidSolutionDecoration
from nti.assessment.interfaces import IQAssignmentSubmissionPendingAssessment
from nti.assessment.interfaces import IQSurvey
from nti.assessment.interfaces import IQuestion
from nti.assessment.interfaces import IQAssignment
from nti.assessment.interfaces import IQEvaluation
from nti.assessment.interfaces import IQuestionSet
from nti.assessment.interfaces import IQAssessedPart
from nti.assessment.interfaces import IQUploadedFile
from nti.assessment.interfaces import IQSubmittedPart
from nti.assessment.interfaces import IQAssignmentPart
from nti.assessment.interfaces import IQAssessedQuestion
from nti.assessment.interfaces import IQuestionSubmission
from nti.assessment.interfaces import IQAssessedQuestionSet
from nti.assessment.interfaces import IQuestionSetSubmission
from nti.assessment.interfaces import IQPartSolutionsExternalizer
from nti.assessment.interfaces import IQPoll

from nti.assessment.interfaces import IQPollSubmission
from nti.assessment.interfaces import IQSurveySubmission

from nti.assessment.interfaces import IQPart
from nti.assessment.interfaces import IRegEx
from nti.assessment.interfaces import IQFillInTheBlankShortAnswerPart
from nti.assessment.interfaces import IQFillInTheBlankWithWordBankPart
from nti.assessment.interfaces import IQFillInTheBlankShortAnswerSolution
from nti.assessment.interfaces import IQFillInTheBlankWithWordBankSolution

from nti.assessment.response import QUploadedFile
from nti.assessment.response import QUploadedImageFile

from nti.externalization.datastructures import InterfaceObjectIO
from nti.externalization.datastructures import ModuleScopedInterfaceObjectIO

from nti.externalization.externalization import to_external_object

from nti.externalization.interfaces import IInternalObjectExternalizer

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import StandardInternalFields

from nti.mimetype.externalization import decorateMimeType

from nti.ntiids.ntiids import TYPE_OID
from nti.ntiids.ntiids import is_ntiid_of_type

from nti.publishing.interfaces import IPublishable

from nti.recorder.interfaces import IRecordable

ID = StandardExternalFields.ID
OID = StandardExternalFields.OID
NTIID = StandardExternalFields.NTIID
MIMETYPE = StandardExternalFields.MIMETYPE
CONTAINER_ID_EXT = StandardExternalFields.CONTAINER_ID
CONTAINER_ID_INT = StandardInternalFields.CONTAINER_ID

logger = __import__('logging').getLogger(__name__)


# Base internal IO


class _AssessmentInternalObjectIOBase(InterfaceObjectIO):
    """
    Base class to customize object IO. See zcml.
    """

    @classmethod
    def _ap_compute_external_class_name_from_interface_and_instance(cls, iface, impl):
        result = getattr(impl, '__external_class_name__', None)
        if not result:
            # Strip off 'IQ' if it's not 'IQuestionXYZ'
            if not iface.__name__.startswith('IQuestion'):
                result = iface.__name__[2:]
            else:
                result = iface.__name__[1:]
            # Strip NonGradable
            idx = result.find('NonGradable')
            if idx >= 0:
                result = result[0:idx] + result[idx + 11:]
        return result

    @classmethod
    def _ap_compute_external_class_name_from_concrete_class(cls, a_type):
        k = a_type.__name__
        ext_class_name = k[1:] if not k.startswith('Question') else k
        return ext_class_name

    def updateFromExternalObject(self, parsed, *args, **kwargs):
        result = super(_AssessmentInternalObjectIOBase, self).updateFromExternalObject(parsed, *args, **kwargs)
        hook = ntiid_object_hook(self._ext_replacement(), parsed)
        return result or hook


# Solution parts


@component.adapter(IQPart)
@interface.implementer(IQPartSolutionsExternalizer)
class _DefaultPartSolutionsExternalizer(object):

    def __init__(self, part):
        self.part = part

    def to_external_object(self):
        return to_external_object(self.part.solutions)


@interface.implementer(IQPartSolutionsExternalizer)
@component.adapter(IQFillInTheBlankShortAnswerPart)
class _FillInTheBlankShortAnswerPartSolutionsExternalizer(object):

    def __init__(self, part):
        self.part = part

    def to_external_object(self):
        result = []
        for solution in self.part.solutions:
            ext = to_external_object(solution)
            if IQFillInTheBlankShortAnswerSolution.providedBy(solution):
                value = {}
                for k, v in solution.value.items():
                    txt = v.solution if IRegEx.providedBy(v) else v
                    value[k] = txt
                ext['value'] = value
        return result


@interface.implementer(IQPartSolutionsExternalizer)
@component.adapter(IQFillInTheBlankWithWordBankPart)
class _FillInTheBlankWithWordBankPartSolutionsExternalizer(object):

    def __init__(self, part):
        self.part = part

    def to_external_object(self):
        result = []
        for solution in self.part.solutions:
            ext = to_external_object(solution)
            if IQFillInTheBlankWithWordBankSolution.providedBy(solution):
                value = ext.get('value', {})
                for k in list(value.keys()):
                    v = value.get(k)
                    if      v and not isinstance(v, six.string_types) \
                        and isinstance(v, Sequence):
                        value[k] = v[0]  # pick first one always
            result.append(ext)
        return result


# Question Sets


@component.adapter(IQuestionSet)
@interface.implementer(IInternalObjectExternalizer)
class _QuestionSetExternalizer(InterfaceObjectIO):

    _excluded_out_ivars_ = frozenset(
        getattr(InterfaceObjectIO, '_excluded_out_ivars_').union({'questions'})
    )

    _ext_iface_upper_bound = IQuestionSet

    def toExternalObject(self, **kwargs):  # pylint: disable=arguments-differ
        context = self._ext_replacement()
        result = super(_QuestionSetExternalizer, self).toExternalObject(**kwargs)
        if 'questions' not in result:
            result['questions'] = questions = []
            for question in context.Items:  # resolve weaf refs
                questions.append(to_external_object(question, **kwargs))
        return result


@interface.implementer(IInternalObjectExternalizer)
class _BasicSummaryExternalizer(InterfaceObjectIO):

    def toExternalObject(self, *args, **kwargs):  # pylint: disable=arguments-differ
        result = super(_BasicSummaryExternalizer, self).toExternalObject(*args, **kwargs)
        result['IsSummary'] = True
        return result


@interface.implementer(IInternalObjectExternalizer)
class _QPartExternalizer(ModuleScopedInterfaceObjectIO):
    """
    Removed by default, and decorated when appropriate for the given
    context.
    """

    _ext_iface_upper_bound = IQPart
    _ext_search_module = assessment_interfaces

    def toExternalObject(self, *args, **kwargs):  # pylint: disable=arguments-differ
        result = super(_QPartExternalizer, self).toExternalObject(*args, **kwargs)
        for key in ('solutions', 'explanation'):
            if key in result:
                result[key] = None
        return result


@interface.implementer(IInternalObjectExternalizer)
class _QPartWithSolutionsExternalizer(ModuleScopedInterfaceObjectIO):
    """
    Version that can be used to expose underlying solutions, e.g for
    certain privileged users.
    """

    _ext_iface_upper_bound = IQPart
    _ext_search_module = assessment_interfaces

    def toExternalObject(self, *args, **kwargs):  # pylint: disable=arguments-differ
        return super(_QPartWithSolutionsExternalizer, self).toExternalObject(*args, **kwargs)


@interface.implementer(IAvoidSolutionDecoration)
class _AvoidSolutionDecorationProxy(SpecificationDecoratorBase):
    """
    Marker interface used to indicate we should avoid solution decoration
    (e.g. for QuestionSet objects when solution decoration will be handled
    in the context of the assignment)
    """


class _AssignmentPartAvoidSolutionDecorationProxy(SpecificationDecoratorBase):

    def __getattr__(self, item):
        result = SpecificationDecoratorBase.__getattr__(self, item)

        if item == "question_set":
            return _AvoidSolutionDecorationProxy(result)

        return result


@interface.implementer(IInternalObjectExternalizer)
class _QAssignmentExternalizer(ModuleScopedInterfaceObjectIO):
    """
    Provides context for question sets during decoration to indicate
    solutions externalization will be handled at the assignment level
    """

    _ext_iface_upper_bound = IQAssignment
    _ext_search_module = assessment_interfaces

    def _ext_getattr(self, ext_self, k, *args, **kwargs):
        result = ModuleScopedInterfaceObjectIO._ext_getattr(self, ext_self, k, *args, **kwargs)

        if k == "parts" and result:
            return [_AssignmentPartAvoidSolutionDecorationProxy(x) for x in result]

        return result


@interface.implementer(IInternalObjectExternalizer)
class QAssignmentSubmissionPendingAssessmentExternalizer(ModuleScopedInterfaceObjectIO):
    """
    Provides context for assessed question sets during decoration to
    indicate solutions externalization will be handled at the assignment
    submission level
    """

    _ext_iface_upper_bound = IQAssignmentSubmissionPendingAssessment
    _ext_search_module = assessment_interfaces

    def _ext_getattr(self, ext_self, k, *args, **kwargs):
        result = ModuleScopedInterfaceObjectIO._ext_getattr(self, ext_self, k, *args, **kwargs)

        if k == "parts" and result:
            return [_AvoidSolutionDecorationProxy(x) for x in result]

        return result


@component.adapter(IQSurvey)
@interface.implementer(IInternalObjectExternalizer)
class _SurveySummaryExternalizer(_BasicSummaryExternalizer):

    _excluded_out_ivars_ = frozenset(('questions',))

    _ext_iface_upper_bound = IQuestionSet


@component.adapter(IQuestionSet)
@interface.implementer(IInternalObjectExternalizer)
class _QuestionSetSummaryExternalizer(_BasicSummaryExternalizer):

    _excluded_out_ivars_ = frozenset(('questions',))

    _ext_iface_upper_bound = IQuestionSet


@component.adapter(IQAssignmentPart)
@interface.implementer(IInternalObjectExternalizer)
class _AssignmentPartSummaryExternalizer(_BasicSummaryExternalizer):

    _excluded_out_ivars_ = frozenset(('question_set',))

    _ext_iface_upper_bound = IQAssignmentPart


# Submission and Assessed objects


@interface.implementer(IInternalObjectExternalizer)
class _QContainedObjectExternalizer(object):

    interface = None

    def __init__(self, item):
        self.item = item

    def toExternalObject(self, **kwargs):
        if hasattr(self.item, 'sublocations'):
            # sets the full parent lineage for these objects.
            # we wrap the execution of it in a tuple in case it
            # returns a generator
            tuple(self.item.sublocations())
        return InterfaceObjectIO(self.item, self.interface).toExternalObject(**kwargs)


@component.adapter(IQSubmittedPart)
class _QSubmittedPartExternalizer(_QContainedObjectExternalizer):
    interface = IQSubmittedPart


@component.adapter(IQAssessedPart)
class _QAssessedPartExternalizer(_QContainedObjectExternalizer):
    interface = IQAssessedPart

    def toExternalObject(self, **kwargs):
        result = super(_QAssessedPartExternalizer, self).toExternalObject(**kwargs)
        result.pop('assessedValue')
        return result


@component.adapter(IQuestionSubmission)
class _QuestionSubmissionExternalizer(_QContainedObjectExternalizer):
    interface = IQuestionSubmission


@component.adapter(IQuestionSetSubmission)
class _QuestionSetSubmissionExternalizer(_QContainedObjectExternalizer):
    interface = IQuestionSetSubmission


@component.adapter(IQAssessedQuestion)
class _QAssessedQuestionExternalizer(_QContainedObjectExternalizer):
    interface = IQAssessedQuestion


@component.adapter(IQAssessedQuestionSet)
class _QAssessedQuestionSetExternalizer(_QContainedObjectExternalizer):
    interface = IQAssessedQuestionSet


@component.adapter(IQPollSubmission)
class _QPollSubmissionExternalizer(_QContainedObjectExternalizer):
    interface = IQPollSubmission


@component.adapter(IQSurveySubmission)
class _QSurveySubmissionSubmissionExternalizer(_QContainedObjectExternalizer):
    interface = IQSurveySubmission


# File uploads

from nti.namedfile.datastructures import BaseFactory
from nti.namedfile.datastructures import NamedFileObjectIO


@component.adapter(IQUploadedFile)
class _QUploadedFileObjectIO(NamedFileObjectIO):

    _excluded_in_ivars_ = frozenset(
        {'download_url', 'url', 'value'}.union(NamedFileObjectIO._excluded_in_ivars_)
    )

    def _ext_mimeType(self, *unused_args):  # pylint: disable=arguments-differ
        return 'application/vnd.nextthought.assessment.uploadedfile'

    def toExternalObject(self, *args, **kwargs):  # pylint: disable=arguments-differ
        ext_dict = super(_QUploadedFileObjectIO, self).toExternalObject(*args, **kwargs)
        return ext_dict


def _QUploadedFileFactory(ext_obj):
    return BaseFactory(ext_obj, QUploadedFile, QUploadedImageFile)


# custom externalization


@component.adapter(IQEvaluation)
@interface.implementer(IInternalObjectExternalizer)
class _EvaluationExporter(object):

    externalizer_name = ''  # default

    def __init__(self, obj):
        self.evaluation = obj

    def _decorate_callback(self, obj, result):
        if isinstance(result, Mapping) and MIMETYPE not in result:
            decorateMimeType(obj, result)

    def _remover(self, result):
        if isinstance(result, Mapping):
            for name, value in list(result.items()):
                if name in (ID, OID, CONTAINER_ID_EXT, CONTAINER_ID_INT):
                    result.pop(name, None)
                elif name == NTIID and is_ntiid_of_type(value, TYPE_OID):
                    result.pop(name, None)
                else:
                    self._remover(value)
        elif isinstance(result, (list, tuple)):
            for value in result:
                self._remover(value)
        return result

    def toExternalObject(self, **kwargs):
        mod_args = dict(**kwargs)
        mod_args['name'] = self.externalizer_name
        mod_args['decorate'] = False  # no decoration
        mod_args['decorate_callback'] = self._decorate_callback
        result = to_external_object(self.evaluation, **mod_args)
        result = self._remover(result)
        if IRecordable.providedBy(self.evaluation):
            result['isLocked'] = self.evaluation.isLocked()
        if IPublishable.providedBy(self.evaluation):
            result['isPublished'] = self.evaluation.isPublished()
        return result


@component.adapter(IQPoll)
@component.adapter(IQuestion)
@component.adapter(IQAssignment)
@interface.implementer(IInternalObjectExternalizer)
class EvalWithPartsExporter(_EvaluationExporter):

    # Ensure our solutions are externalized
    externalizer_name = 'solutions'

    def _remove_part_ntiids(self, result):
        for part in result.get('parts') or ():
            if isinstance(part, Mapping):
                part.pop(NTIID, None)
                part.pop(NTIID.lower(), None)
        return result

    def toExternalObject(self, **kwargs):
        result = _EvaluationExporter.toExternalObject(self, **kwargs)
        return self._remove_part_ntiids(result)
_EvalWithPartsExporter = EvalWithPartsExporter


@component.adapter(IQuestionSet)
@interface.implementer(IInternalObjectExternalizer)
class _QuestionSetExporter(_EvalWithPartsExporter):

    def toExternalObject(self, **kwargs):
        result = _EvalWithPartsExporter.toExternalObject(self, **kwargs)
        for question in result.get('questions') or ():
            if isinstance(question, Mapping):
                self._remove_part_ntiids(question)
        return result
