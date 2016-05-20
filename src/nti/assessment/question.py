#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Code related to the question interfaces.

.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.container.contained import Contained

from zope.interface.common.sequence import IFiniteSequence

from zope.mimetype.interfaces import IContentTypeAware

from persistent import Persistent
from persistent.list import PersistentList

from nti.assessment.common import get_containerId
from nti.assessment.common import AssessmentSchemaMixin

from nti.assessment.interfaces import QUESTION_MIME_TYPE
from nti.assessment.interfaces import QUESTION_SET_MIME_TYPE
from nti.assessment.interfaces import QUESTION_FILL_IN_THE_BLANK_MIME_TYPE

from nti.assessment.interfaces import IQuestion
from nti.assessment.interfaces import IQuestionSet
from nti.assessment.interfaces import IQFillInTheBlankWithWordBankQuestion

from nti.common.property import alias
from nti.common.property import readproperty

from nti.coremetadata.mixins import RecordableMixin
from nti.coremetadata.mixins import PublishableMixin
from nti.coremetadata.mixins import RecordableContainerMixin

from nti.dataserver_core.interfaces import IContained as INTIContained

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import EqHash

from nti.wref.interfaces import IWeakRef

@interface.implementer(INTIContained,
					   IFiniteSequence,
					   IContentTypeAware,
					   IAttributeAnnotatable)
class QBaseMixin(SchemaConfigured,
				 Persistent,
				 RecordableMixin,
				 PublishableMixin,
				 Contained,
				 AssessmentSchemaMixin):

	ntiid = None
	id = alias('ntiid')

	parameters = {}  # IContentTypeAware

	def __init__(self, *args, **kwargs):
		Persistent.__init__(self)
		SchemaConfigured.__init__(self, *args, **kwargs)

	@readproperty
	def __home__(self):
		return self.__parent__

	@readproperty
	def containerId(self):
		return get_containerId(self)

@interface.implementer(IQuestion)
@EqHash('content', 'parts', superhash=True)
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

@EqHash('title', 'questions', superhash=True)
@interface.implementer(IQuestionSet)
class QQuestionSet(QBaseMixin, RecordableContainerMixin):

	questions = ()
	parts = alias('questions')

	createDirectFieldProperties(IQuestionSet)

	title = AdaptingFieldProperty(IQuestionSet['title'])

	mimeType = mime_type = QUESTION_SET_MIME_TYPE

	@property
	def Items(self):
		for question in self.questions or ():
			question = question() if IWeakRef.providedBy(question) else question
			if question is not None:
				yield question

	def __getitem__(self, index):
		return self.questions[index]

	def __len__(self):
		return len(self.questions or ())

	def pop(self, index):
		return self.questions.pop( index )

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
		item.__parent__ = self  # take ownership
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
			item.__parent__ = self  # take ownership
			self.questions.insert(index, item)

@EqHash('wordbank', include_super=True)
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
