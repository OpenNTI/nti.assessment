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

from persistent.list import PersistentList

from ZODB.POSException import ConnectionStateError

from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.cachedescriptors.property import readproperty

from zope.interface.common.sequence import IFiniteSequence

from zope.mimetype.interfaces import IContentTypeAware

from nti.assessment.common import get_containerId

from nti.assessment.common import VersionedMixin
from nti.assessment.common import EvaluationSchemaMixin

from nti.assessment.interfaces import QUESTION_MIME_TYPE
from nti.assessment.interfaces import QUESTION_SET_MIME_TYPE
from nti.assessment.interfaces import QUESTION_FILL_IN_THE_BLANK_MIME_TYPE

from nti.assessment.interfaces import IQuestion
from nti.assessment.interfaces import IQuestionSet
from nti.assessment.interfaces import IQFillInTheBlankWithWordBankQuestion

from nti.assessment.randomized.interfaces import IRandomizedPartsContainer

from nti.assessment.randomized_proxy import QuestionRandomizedPartsProxy

from nti.coremetadata.interfaces import IContained as INTIContained

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.externalization.externalization import to_external_object

from nti.externalization.persistence import NoPickle

from nti.property.property import alias

from nti.publishing.mixins import PublishableMixin

from nti.recorder.mixins import RecordableMixin
from nti.recorder.mixins import RecordableContainerMixin

from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.wref.interfaces import IWeakRef

logger = __import__('logging').getLogger(__name__)


@interface.implementer(INTIContained,
                       IFiniteSequence,
                       IContentTypeAware,
                       IAttributeAnnotatable)
class QBaseMixin(SchemaConfigured,
                 PersistentCreatedModDateTrackingObject,
                 RecordableMixin,
                 PublishableMixin,
                 VersionedMixin,
                 EvaluationSchemaMixin):

    tags = ()
    id = alias('ntiid')

    __parent__ = None

    parameters = {}  # IContentTypeAware

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
        SchemaConfigured.__init__(self, *args, **kwargs)
        PersistentCreatedModDateTrackingObject.__init__(self)

    @readproperty
    def __name__(self):
        return self.ntiid

    @readproperty
    def __home__(self):
        return self.__parent__

    @readproperty
    def containerId(self):
        return get_containerId(self)

    def __str__(self):
        try:
            result = "%s(ntiid=%s)" % (self.__class__.__name__, self.ntiid)
            return result
        except (ConnectionStateError, AttributeError):
            return"<%s object at %s>" % (type(self).__name__, hex(id(self)))
    __repr__ = __str__


@interface.implementer(IQuestion)
class QQuestion(QBaseMixin):

    parts = ()
    content = None

    createDirectFieldProperties(IQuestion)

    mimeType = mime_type = QUESTION_MIME_TYPE

    def __getitem__(self, index):
        return self.parts[index]

    def __len__(self):
        return len(self.parts or ())

    def __setattr__(self, name, value):
        super(QQuestion, self).__setattr__(name, value)
        if name == "parts":
            for x in self.parts or ():
                x.__parent__ = self  # take ownership


@NoPickle
class _QuestionIterableWrapper(Sequence):
    """
    A wrapper to a sequence of questions that ensures possible
    weak refs are resolved.
    """

    __slots__ = ('_storage',)

    def __init__(self, questions):
        self._storage = questions

    def __len__(self):
        return len(self._storage)

    def _transform(self, question):
        if IWeakRef.providedBy(question):
            question = question()
        return question

    def __getitem__(self, index):
        result = self._storage[index]
        return self._transform(result)

    def toExternalObject(self, *args, **kwargs):
        return tuple(to_external_object(x, *args, **kwargs) for x in self)


@NoPickle
class _ProxyQuestionIterableWrapper(_QuestionIterableWrapper):
    """
    Used by :class:`IRandomizedPartsContainer` question sets, this will
    return :class:`QuestionRandomizedPartsProxy` question objects.
    """

    def _transform(self, question):
        result = super(_ProxyQuestionIterableWrapper, self)._transform(question)
        if result is not None:
            result = QuestionRandomizedPartsProxy(result)
        return result


@interface.implementer(IQuestionSet)
class QQuestionSet(QBaseMixin, RecordableContainerMixin):

    parts = alias('questions')

    createDirectFieldProperties(IQuestionSet)

    title = AdaptingFieldProperty(IQuestionSet['title'])

    mimeType = mime_type = QUESTION_SET_MIME_TYPE

    @property
    def _questions(self):
        return self.__dict__.get('questions')

    @_questions.setter
    def _questions(self, val):
        self.__dict__['questions'] = val

    @property
    def questions(self):
        result = self._questions
        if result:
            if IRandomizedPartsContainer.providedBy(self):
                result = _ProxyQuestionIterableWrapper(result)
            else:
                result = _QuestionIterableWrapper(result)
        return result

    @questions.setter
    def questions(self, val):
        val = PersistentList(val) if val is not None else val
        self.__dict__['questions'] = val
        self._p_changed = True

    @property
    def Items(self):
        return iter(self.questions or ())

    def __getitem__(self, index):
        return self.questions[index]

    def get_question_by_ntiid(self, ntiid):
        for question in self.questions or ():
            if ntiid == question.ntiid:
                return question

    def __len__(self):
        return len(self.questions or ())

    def pop(self, index):
        try:
            return self._questions.pop(index)
        except (TypeError, AttributeError):
            raise IndexError()

    def remove(self, question):
        ntiid = getattr(question, 'ntiid', question)
        for idx, question in enumerate(tuple(self.questions or ())):  # mutating
            if question.ntiid == ntiid:
                return self.pop(idx)
        return None

    def _validate_insert(self, item):
        return item

    def append(self, item):
        item = self._validate_insert(item)
        if '_questions' not in self.__dict__:
            self._questions = PersistentList()
        self._questions.append(item)
    add = append

    def insert(self, index, item):
        # Remove from our list if it exists, and then insert at.
        self.remove(item)
        # Only validate after remove.
        item = self._validate_insert(item)
        if index is None or index >= len(self):
            # Default to append.
            self.append(item)
        else:
            self._questions.insert(index, item)

    @property
    def question_count(self):
        return len(self)


@interface.implementer(IQFillInTheBlankWithWordBankQuestion)
class QFillInTheBlankWithWordBankQuestion(QQuestion):

    __external_class_name__ = "Question"
    mime_type = mimeType = QUESTION_FILL_IN_THE_BLANK_MIME_TYPE

    createDirectFieldProperties(IQFillInTheBlankWithWordBankQuestion)

    wordBank = alias('wordbank')

    def __setattr__(self, name, value):
        super(QFillInTheBlankWithWordBankQuestion, self).__setattr__(name, value)
        if name == "parts":
            for x in self.parts or ():
                x.__parent__ = self  # take ownership
