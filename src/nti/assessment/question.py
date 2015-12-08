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

from zope.location.interfaces import ISublocations

from zope.mimetype.interfaces import IContentTypeAware

from persistent import Persistent

from nti.common.property import alias

from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import EqHash

from .interfaces import IQuestion
from .interfaces import IQuestionSet
from .interfaces import IQFillInTheBlankWithWordBankQuestion

from .interfaces import QUESTION_SET_MIME_TYPE

@interface.implementer(IQuestion,
					   IFiniteSequence,
					   IContentTypeAware,
					   IAttributeAnnotatable)
@EqHash('content', 'parts', superhash=True)
class QQuestion(Contained,
				SchemaConfigured,
				Persistent):

	parts = ()
	ntiid = None
	content = None

	createDirectFieldProperties(IQuestion)

	mimeType = mime_type = 'application/vnd.nextthought.naquestion'

	def __init__(self, *args, **kwargs):
		Persistent.__init__(self)
		SchemaConfigured.__init__(self, *args, **kwargs)

	def __getitem__(self, index):
		return self.parts[index]

	def __len__(self):
		return len(self.parts or ())

@interface.implementer(IQuestionSet,
					   ISublocations,
					   IFiniteSequence,
					   IContentTypeAware,
					   IAttributeAnnotatable)
@EqHash('title', 'questions', superhash=True)
class QQuestionSet(Contained,
				   SchemaConfigured,
				   Persistent):

	ntiid = None
	questions = ()
	parts = alias('questions')

	createDirectFieldProperties(IQuestionSet)

	title = AdaptingFieldProperty(IQuestionSet['title'])

	mimeType = mime_type = QUESTION_SET_MIME_TYPE

	def __init__(self, *args, **kwargs):
		Persistent.__init__(self)
		SchemaConfigured.__init__(self, *args, **kwargs)

	def sublocations(self):
		for question in self.questions or ():
			yield question

	def __getitem__(self, index):
		return self.questions[index]

	def __len__(self):
		return len(self.questions or ())

@interface.implementer(IQFillInTheBlankWithWordBankQuestion)
@EqHash('wordbank', include_super=True)
class QFillInTheBlankWithWordBankQuestion(QQuestion):
	createDirectFieldProperties(IQFillInTheBlankWithWordBankQuestion)

	__external_class_name__ = "Question"
	mime_type = mimeType = 'application/vnd.nextthought.naquestionfillintheblankwordbank'

	wordBank = alias('wordbank')

	def __setattr__(self, name, value):
		super(QFillInTheBlankWithWordBankQuestion, self).__setattr__(name, value)
		if name == "parts":
			for x in self.parts or ():
				x.__parent__ = self  # take ownership

	def sublocations(self):
		for part in self.parts or ():
			yield part
