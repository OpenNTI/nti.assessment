#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

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

from nti.coremetadata.interfaces import IContained as INTIContained

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.property.property import alias

from nti.publishing.mixins import PublishableMixin

from nti.recorder.mixins import RecordableMixin
from nti.recorder.mixins import RecordableContainerMixin

from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.wref.interfaces import IWeakRef
from nti.assessment.randomized.interfaces import IRandomizedPartsContainer
from nti.assessment.randomized_proxy import QuestionRandomizedPartsProxy

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


@interface.implementer(IQuestionSet)
class QQuestionSet(QBaseMixin, RecordableContainerMixin):

    questions = ()
    parts = alias('questions')

    createDirectFieldProperties(IQuestionSet)

    title = AdaptingFieldProperty(IQuestionSet['title'])

    mimeType = mime_type = QUESTION_SET_MIME_TYPE

    def _maybe_proxy_wrap_question(self, question):
        """
        Return randomized part question proxy based on our
        state.
        """
        result = question
        if      question is not None \
            and IRandomizedPartsContainer.providedBy(self):
            result = QuestionRandomizedPartsProxy(question)
        return result

    @property
    def Items(self):
        for question in self.questions or ():
            question = question() if IWeakRef.providedBy(question) else question
            if question is not None:
                question = self._maybe_proxy_wrap_question(question)
                yield question

    def __getitem__(self, index):
        question = self.questions[index]
        question = self._maybe_proxy_wrap_question(question)
        return question

    def get_question_by_ntiid(self, ntiid):
        for question in self.Items:
            if ntiid == question.ntiid:
                return question

    def __len__(self):
        return len(self.questions or ())

    def pop(self, index):
        question = self.questions.pop(index)
        question = self._maybe_proxy_wrap_question(question)
        return question

    def remove(self, question):
        ntiid = getattr(question, 'ntiid', question)
        for idx, question in enumerate(tuple(self.questions)):  # mutating
            if question.ntiid == ntiid:
                return self.questions.pop(idx)
        return None

    def _validate_insert(self, item):
        return item

    def append(self, item):
        item = self._validate_insert(item)
        self.questions = PersistentList() if not self.questions else self.questions
        self.questions.append(item)
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
            self.questions.insert(index, item)

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
