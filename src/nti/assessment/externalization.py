#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
from collections import Mapping
from collections import Sequence

from zope import component
from zope import interface

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

from nti.externalization.externalization import to_external_object

from nti.externalization.interfaces import IInternalObjectIO
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


# Base internal IO


@interface.implementer(IInternalObjectIO)
class _AssessmentInternalObjectIOBase(object):
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

    _excluded_out_ivars_ = getattr(InterfaceObjectIO, '_excluded_out_ivars_').union({'questions'})

    _ext_iface_upper_bound = IQuestionSet

    def toExternalObject(self, **kwargs):
        context = self._ext_replacement()
        result = super(_QuestionSetExternalizer, self).toExternalObject(**kwargs)
        if 'questions' not in result:
            result['questions'] = questions = []
            for question in context.Items:  # resolve weaf refs
                questions.append(to_external_object(question, **kwargs))
        return result


@interface.implementer(IInternalObjectExternalizer)
class _BasicSummaryExternalizer(InterfaceObjectIO):

    def toExternalObject(self, *args, **kwargs):
        result = super(_BasicSummaryExternalizer, self).toExternalObject(*args, **kwargs)
        result['IsSummary'] = True
        return result


@component.adapter(IQSurvey)
@interface.implementer(IInternalObjectExternalizer)
class _SurveySummaryExternalizer(_BasicSummaryExternalizer):

    _excluded_out_ivars_ = ('questions',)

    _ext_iface_upper_bound = IQuestionSet


@component.adapter(IQuestionSet)
@interface.implementer(IInternalObjectExternalizer)
class _QuestionSetSummaryExternalizer(_BasicSummaryExternalizer):

    _excluded_out_ivars_ = ('questions',)

    _ext_iface_upper_bound = IQuestionSet


@component.adapter(IQAssignmentPart)
@interface.implementer(IInternalObjectExternalizer)
class _AssignmentPartSummaryExternalizer(_BasicSummaryExternalizer):

    _excluded_out_ivars_ = ('question_set',)

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

    _excluded_in_ivars_ = {'download_url', 'url', 'value'}.union(NamedFileObjectIO._excluded_in_ivars_)

    def _ext_mimeType(self, _):
        return 'application/vnd.nextthought.assessment.uploadedfile'

    def toExternalObject(self, *args, **kwargs):
        ext_dict = super(_QUploadedFileObjectIO, self).toExternalObject(*args, **kwargs)
        return ext_dict


def _QUploadedFileFactory(ext_obj):
    factory = BaseFactory(ext_obj, QUploadedFile, QUploadedImageFile)
    return factory


# custom externalization


@component.adapter(IQEvaluation)
@interface.implementer(IInternalObjectExternalizer)
class _EvaluationExporter(object):

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
        mod_args['name'] = ''  # default
        mod_args['decorate'] = False  # no decoration
        mod_args['decorate_callback'] = self._decorate_callback
        result = to_external_object(self.evaluation, **mod_args)
        result = self._remover(result)
        if IRecordable.providedBy(self.evaluation):
            result['isLocked'] = self.evaluation.isLocked()
        if IPublishable.providedBy(self.evaluation):
            result['isPublished'] = self.evaluation.isPublished()
        return result


@component.adapter(IQuestion)
@component.adapter(IQAssignment)
@interface.implementer(IInternalObjectExternalizer)
class _EvalWithPartsExporter(_EvaluationExporter):

    def _remove_part_ntiids(self, result):
        for part in result.get('parts') or ():
            if isinstance(part, Mapping):
                part.pop(NTIID, None)
                part.pop(NTIID.lower(), None)
        return result

    def toExternalObject(self, **kwargs):
        result = _EvaluationExporter.toExternalObject(self, **kwargs)
        return self._remove_part_ntiids(result)


@component.adapter(IQuestionSet)
@interface.implementer(IInternalObjectExternalizer)
class _QuestionSetExporter(_EvalWithPartsExporter):

    def toExternalObject(self, **kwargs):
        result = _EvalWithPartsExporter.toExternalObject(self, **kwargs)
        for question in result.get('questions') or ():
            if isinstance(question, Mapping):
                self._remove_part_ntiids(question)
        return result
