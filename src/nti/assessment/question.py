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

from nti.assessment._util import get_containerId

from nti.assessment.interfaces import QUESTION_MIME_TYPE
from nti.assessment.interfaces import QUESTION_SET_MIME_TYPE
from nti.assessment.interfaces import QUESTION_FILL_IN_THE_BLANK_MIME_TYPE

from nti.assessment.interfaces import IQuestion
from nti.assessment.interfaces import IQuestionSet
from nti.assessment.interfaces import IQFillInTheBlankWithWordBankQuestion

from nti.common.property import alias
from nti.common.property import readproperty

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
class QBaseMixin(Contained,
				 SchemaConfigured,
				 Persistent):

	ntiid = None
	id = alias('ntiid')
	home = alias('__parent__')

	parameters = {}  # IContentTypeAware

	def __init__(self, *args, **kwargs):
		Persistent.__init__(self)
		SchemaConfigured.__init__(self, *args, **kwargs)

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

@EqHash('title', 'questions', superhash=True)
@interface.implementer(IQuestionSet)
class QQuestionSet(QBaseMixin):

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

	def sublocations(self):
		for part in self.parts or ():
			yield part
