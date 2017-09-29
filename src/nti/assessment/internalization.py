#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six
import collections
from curses.ascii import isctrl

from zope import component
from zope import interface

from nti.assessment.interfaces import DISCLOSURE_TERMINATION, IQFreeResponsePart

from nti.assessment.interfaces import IRegEx
from nti.assessment.interfaces import IQuestion
from nti.assessment.interfaces import IQInquiry
from nti.assessment.interfaces import IQFilePart
from nti.assessment.interfaces import IWordEntry
from nti.assessment.interfaces import IQMatchingPart
from nti.assessment.interfaces import IQMultipleChoicePart
from nti.assessment.interfaces import IQMatchingSolution
from nti.assessment.interfaces import IQModeledContentResponse
from nti.assessment.interfaces import IQMultipleChoiceSolution
from nti.assessment.interfaces import IQMultipleChoiceMultipleAnswerPart
from nti.assessment.interfaces import IQFillInTheBlankShortAnswerSolution
from nti.assessment.interfaces import IQFillInTheBlankWithWordBankSolution
from nti.assessment.interfaces import IQMultipleChoiceMultipleAnswerSolution

from nti.assessment.parts import QFilePart
from nti.assessment.parts import QMatchingPart
from nti.assessment.parts import QFreeResponsePart
from nti.assessment.parts import QMultipleChoicePart
from nti.assessment.parts import QMultipleChoiceMultipleAnswerPart

from nti.assessment.question import QQuestion

from nti.assessment.solution import QMatchingSolution
from nti.assessment.solution import QMultipleChoiceSolution
from nti.assessment.solution import QMultipleChoiceMultipleAnswerSolution

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import IClassObjectFactory
from nti.externalization.interfaces import IInternalObjectUpdater

from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

logger = __import__('logging').getLogger(__name__)


@component.adapter(IWordEntry)
@interface.implementer(IInternalObjectUpdater)
class _WordEntryUpdater(object):

    __slots__ = ('obj',)

    def __init__(self, obj):
        self.obj = obj

    def updateFromExternalObject(self, parsed, *unused_args, **unused_kwargs):
        if 'content' not in parsed or not parsed['content']:
            parsed['content'] = parsed['word']
        if parsed.get('lang'):
            parsed['lang'] = parsed['lang'].lower()
        result = InterfaceObjectIO(
                    self.obj,
                    IWordEntry).updateFromExternalObject(parsed)
        return result


@interface.implementer(IInternalObjectUpdater)
@component.adapter(IQFillInTheBlankShortAnswerSolution)
class _QFillInTheBlankShortAnswerSolutionUpdater(object):

    __slots__ = ('obj',)

    def __init__(self, obj):
        self.obj = obj

    def updateFromExternalObject(self, parsed, *unused_args, **unused_kwargs):
        value = parsed.get('value', {})
        for key in tuple(value.keys()):  # mutating
            regex = value.get(key)
            if isinstance(regex, six.string_types):
                regex = IRegEx(regex)
            elif isinstance(regex, collections.Mapping):
                ext_obj = regex
                regex = find_factory_for(ext_obj)()
                update_from_external_object(regex, ext_obj)
            value[key] = regex
        result = InterfaceObjectIO(
                    self.obj,
                    IQFillInTheBlankShortAnswerSolution).updateFromExternalObject(parsed)
        return result


@interface.implementer(IInternalObjectUpdater)
@component.adapter(IQFillInTheBlankWithWordBankSolution)
class _QFillInTheBlankWithWordBankSolutionUpdater(object):

    __slots__ = ('obj',)

    def __init__(self, obj):
        self.obj = obj

    def updateFromExternalObject(self, parsed, *unused_args, **unused_kwargs):
        value = parsed.get('value', {})
        for key in tuple(value.keys()):  # mutating
            data = value.get(key)
            if isinstance(data, six.string_types):
                data = data.split()  # make it a list
                value[key] = data
        result = InterfaceObjectIO(
                    self.obj,
                    IQFillInTheBlankWithWordBankSolution).updateFromExternalObject(parsed)
        return result


@component.adapter(IQModeledContentResponse)
@interface.implementer(IInternalObjectUpdater)
class _QModeledContentResponseUpdater(object):

    __slots__ = ('obj',)

    def __init__(self, obj):
        self.obj = obj

    def updateFromExternalObject(self, parsed, *unused_args, **unused_kwargs):
        value = parsed.get('value', None)
        if value is not None:
            if isinstance(value, six.string_types):
                value = [value]
            for idx in range(len(value)):
                value[idx] = filter(lambda c: not isctrl(c), value[idx])
            parsed['value'] = value
        result = InterfaceObjectIO(
                    self.obj,
                    IQModeledContentResponse).updateFromExternalObject(parsed)
        return result


@component.adapter(IQInquiry)
@interface.implementer(IInternalObjectUpdater)
class _QInquiryUpdater(object):

    __slots__ = ('obj',)

    def __init__(self, obj):
        self.obj = obj

    def updateFromExternalObject(self, parsed, *unused_args, **unused_kwargs):
        value = parsed.get('disclosure', None) or DISCLOSURE_TERMINATION
        parsed['disclosure'] = value.lower()
        result = InterfaceObjectIO(
                    self.obj,
                    IQInquiry).updateFromExternalObject(parsed)
        return result


@interface.implementer(IClassObjectFactory)
class AssessmentFactoryMixin(object):
    factory = None
    provided = None
    description = title = "Assessment object factory"

    def __init__(self, *args):
        pass

    def __call__(self, *unused_args, **unused_kw):
        return self.factory()

    def getInterfaces(self):
        return (self.provided,)


class QuestionFactory(AssessmentFactoryMixin):
    factory = QQuestion
    provided = IQuestion


class FilePartFactory(AssessmentFactoryMixin):
    factory = QFilePart
    provided = IQFilePart


class FreeResponsePartFactory(AssessmentFactoryMixin):
    factory = QFreeResponsePart
    provided = IQFreeResponsePart


class MatchingPartFactory(AssessmentFactoryMixin):
    factory = QMatchingPart
    provided = IQMatchingPart


class MultipleChoicePartFactory(AssessmentFactoryMixin):
    factory = QMultipleChoicePart
    provided = IQMultipleChoicePart


class MultipleChoiceMultipleAnswerPartFactory(AssessmentFactoryMixin):
    factory = QMultipleChoiceMultipleAnswerPart
    provided = IQMultipleChoiceMultipleAnswerPart


class MatchingSolutionFactory(AssessmentFactoryMixin):
    factory = QMatchingSolution
    provided = IQMatchingSolution


class MultipleChoiceSolutionFactory(AssessmentFactoryMixin):
    factory = QMultipleChoiceSolution
    provided = IQMultipleChoiceSolution


class MultipleChoiceMultipleAnswerSolutionFactory(AssessmentFactoryMixin):
    factory = QMultipleChoiceMultipleAnswerSolution
    provided = IQMultipleChoiceMultipleAnswerSolution
