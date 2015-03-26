#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time

from zope import interface
from zope.interface.common.mapping import IWriteMapping
from zope.interface.common.sequence import IFiniteSequence

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.container.contained import Contained

from zope.location.interfaces import ISublocations

from zope.mimetype.interfaces import IContentTypeAware

from persistent import Persistent

from nti.common.property import alias

from nti.coremetadata.interfaces import ICreated
from nti.coremetadata.interfaces import ILastModified

from nti.dataserver.core.mixins import ContainedMixin

from nti.externalization.representation import WithRepr

from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import EqHash

from ._util import make_sublocations as _make_sublocations
from ._util import dctimes_property_fallback as _dctimes_property_fallback 

from .interfaces import IQPoll
from .interfaces import IQSurvey
from .interfaces import IPollSubmission
from .interfaces import IQSubmittedPoll
from .interfaces import IQSubmittedSurvey
from .interfaces import ISurveySubmission

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

@WithRepr
@interface.implementer(IPollSubmission, ISublocations, IFiniteSequence)
class QPollSubmission(SchemaConfigured, Contained):
	createDirectFieldProperties(IPollSubmission)

	sublocations = _make_sublocations()

	def __getitem__(self, idx):
		return self.parts[idx]

	def __setitem__(self, idx, value):
		self.parts[idx] = value
		
	def __delitem__(self, idx):
		del self.parts[idx]
	
	def __len__(self):
		return len(self.parts)
	
@WithRepr
@interface.implementer(ISurveySubmission, ISublocations, IWriteMapping)
class QSurveySubmission(SchemaConfigured, Contained):
	createDirectFieldProperties(ISurveySubmission)

	polls = alias('questions')
	sublocations = _make_sublocations('questions')
	
	def get(self, key, default=None):
		try:
			return self[key]
		except KeyError:
			return default
		
	def index(self, key):
		for idx, poll in enumerate(self.poll or ()):
			if poll.pollId == key:
				return idx
		return -1

	def __getitem__(self, key):
		idx = self.index(key)
		if idx == -1:
			raise KeyError(key)
		return self.polls[idx]
	
	def __delitem__(self, key):
		idx = self.index(key)
		if idx == -1:
			raise KeyError(key)
		del self.polls[idx]
		
	def __setitem__(self, key, value):
		assert key == value.pollId
		idx = self.index(key)
		if idx == -1:
			self.polls.append(value)
		else:
			self.polls[idx] = value

	def __contains__(self, key):
		return self.index(key) != -1
		
	def __len__(self):
		return len(self.polls)

@interface.implementer(IQSubmittedPoll,
					   ICreated,
					   ILastModified,
					   ISublocations)
@EqHash('pollId', 'parts',
		superhash=True)
@WithRepr
class QSubmittedPoll(SchemaConfigured,
					 ContainedMixin,
					 Persistent):
	
	__external_can_create__ = False
	createDirectFieldProperties(IQSubmittedPoll)

	creator = None
	createdTime = _dctimes_property_fallback('createdTime', 'Date.Modified')
	lastModified = _dctimes_property_fallback('lastModified', 'Date.Created')
	
	def __init__(self, *args, **kwargs):
		super(QSubmittedPoll, self).__init__(*args, **kwargs)
		self.lastModified = self.createdTime = time.time()

	def updateLastMod(self, t=None):
		self.lastModified = (t if t is not None and t > self.lastModified else time.time())
		return self.lastModified

	sublocations = _make_sublocations()

@interface.implementer(IQSubmittedSurvey,
					   ICreated,
					   ILastModified)
@EqHash('surveyId', 'questions',
		superhash=True)
@WithRepr
class QSubmittedSurvey(SchemaConfigured,
					   ContainedMixin,
					   Persistent):
	
	__external_can_create__ = False
	createDirectFieldProperties(IQSubmittedSurvey)
	
	creator = None
	createdTime = _dctimes_property_fallback('createdTime', 'Date.Modified')
	lastModified = _dctimes_property_fallback('lastModified', 'Date.Created')

	def __init__(self, *args, **kwargs):
		super(QSubmittedSurvey, self).__init__(*args, **kwargs)
		self.lastModified = self.createdTime = time.time()

	def updateLastMod(self, t=None):
		self.lastModified = (t if t is not None and t > self.lastModified else time.time())
		return self.lastModified
	
	sublocations = _make_sublocations('questions')
