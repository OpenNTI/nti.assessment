#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope.interface.common.sequence import IFiniteSequence

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.container.contained import Contained

from zope.location.interfaces import ISublocations

from zope.mimetype.interfaces import IContentTypeAware

from persistent import Persistent

from nti.common.property import alias

from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import EqHash

from .interfaces import IQPoll
from .interfaces import IQSurvey

@interface.implementer(IQPoll,
					   IFiniteSequence,
					   IContentTypeAware,
					   IAttributeAnnotatable)
@EqHash('content', 'parts', superhash=True)
class QPoll(Contained,
			SchemaConfigured,
			Persistent):

	parts = ()
	content = None

	createDirectFieldProperties(IQPoll)

	mimeType = mime_type = 'application/vnd.nextthought.napoll'

	def __init__(self, *args, **kwargs):
		Persistent.__init__(self)
		SchemaConfigured.__init__(self, *args, **kwargs)
	
	def __getitem__(self, index):
		return self.parts[index]
	
	def __len__(self):
		return len(self.parts or ())

@interface.implementer(IQSurvey,
					   ISublocations,
					   IFiniteSequence,
					   IContentTypeAware,
					   IAttributeAnnotatable)
@EqHash('title', 'questions', superhash=True)
class QSurvey(Contained,
			  SchemaConfigured,
			  Persistent):

	questions = ()
	parts = alias('questions')

	createDirectFieldProperties(IQSurvey)

	title = AdaptingFieldProperty(IQSurvey['title'])

	mimeType = mime_type = 'application/vnd.nextthought.nasurvey'

	def __init__(self, *args, **kwargs):
		Persistent.__init__(self)
		SchemaConfigured.__init__(self, *args, **kwargs)

	def sublocations(self):
		for question in self.questions or ():
			yield question
			
	def __getitem__(self, index):
		return self.parts[index]
	
	def __len__(self):
		return len(self.parts or ())
