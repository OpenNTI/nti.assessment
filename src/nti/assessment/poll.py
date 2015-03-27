#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time

from zope import component
from zope import interface

from zope.interface.common.mapping import IWriteMapping
from zope.interface.common.sequence import IFiniteSequence

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.container.contained import Contained

from zope.location.interfaces import ISublocations

from zope.mimetype.interfaces import IContentTypeAware

from persistent import Persistent
from persistent.list import PersistentList

from nti.common.property import alias

from nti.coremetadata.interfaces import ICreated
from nti.coremetadata.interfaces import ILastModified

from nti.dataserver.core.mixins import ContainedMixin

from nti.externalization.representation import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from ._util import make_sublocations as _make_sublocations
from ._util import dctimes_property_fallback as _dctimes_property_fallback 

from .common import QSubmittedPart

from .interfaces import IQPoll
from .interfaces import IQSurvey
from .interfaces import IQPollSubmission
from .interfaces import IQSubmittedPoll
from .interfaces import IQSubmittedSurvey
from .interfaces import IQSurveySubmission

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
@interface.implementer(IQPollSubmission, ISublocations, IFiniteSequence)
class QPollSubmission(SchemaConfigured, Contained):
	createDirectFieldProperties(IQPollSubmission)

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
@interface.implementer(IQSurveySubmission, ISublocations, IWriteMapping)
class QSurveySubmission(SchemaConfigured, Contained):
	createDirectFieldProperties(IQSurveySubmission)

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
					   ILastModified,
					   ISublocations)
@EqHash('surveyId', 'questions',
		superhash=True)
@WithRepr
class QSubmittedSurvey(SchemaConfigured,
					   ContainedMixin,
					   Persistent):
	
	__external_can_create__ = False
	createDirectFieldProperties(IQSubmittedSurvey)
	
	creator = None
	polls = alias('questions')

	createdTime = _dctimes_property_fallback('createdTime', 'Date.Modified')
	lastModified = _dctimes_property_fallback('lastModified', 'Date.Created')

	def __init__(self, *args, **kwargs):
		super(QSubmittedSurvey, self).__init__(*args, **kwargs)
		self.lastModified = self.createdTime = time.time()

	def updateLastMod(self, t=None):
		self.lastModified = (t if t is not None and t > self.lastModified else time.time())
		return self.lastModified
	
	sublocations = _make_sublocations('questions')

def submitted_poll_submission(submission, registry=component):
	"""
	Register the given poll submission.

	:return: An :class:`.interfaces.IQSubmittedPoll`.
	:param submission: An :class:`.interfaces.IQPollSubmission`.
		The ``parts`` of this submission must be the same length
		as the parts of the poll being submitted. 
	:param registry: If given, an :class:`.IComponents`. If
		not given, the current component registry will be used.
		Used to look up the question set and question by id.
	:raises LookupError: If no question can be found for the submission.
	"""

	poll = registry.getUtility(IQPoll, name=submission.pollId)
	if len(poll.parts) != len(submission.parts):
		raise ValueError("Poll (%s) and submission (%s) have different numbers of parts." %
						 (len(poll.parts), len(submission.parts)))

	parts = PersistentList()
	for sub_part in submission.parts:
		part = QSubmittedPart(submittedResponse=sub_part)
		parts.append(part)

	result = QSubmittedPoll(pollId=submission.pollId, parts=parts)
	return result

def submitted_survey_submission(set_submission, registry=component):
	"""
	Register the given question set submission.

	:return: An :class:`.interfaces.IQSubmittedSurvey`.
	:param set_submission: An :class:`.interfaces.IQSurveySubmission`.
	:param registry: If given, an :class:`.IComponents`. If
		not given, the current component registry will be used.
		Used to look up the question set and question by id.
	:raises LookupError: If no survery can be found for the submission.
	"""

	survey = registry.getUtility(IQSurvey, name=set_submission.surveyId)

	polls_ntiids = {q.ntiid for q in survey.questions}

	submitted = PersistentList()
	for sub_poll in set_submission.questions:
		poll = registry.getUtility(IQPoll, name=sub_poll.pollId )
		if poll in survey.questions or poll.ntiid in polls_ntiids:
			stted_poll = IQSubmittedPoll(sub_poll)
			submitted.append(stted_poll)
		else: # pragma: no cover
			logger.debug("Bad input, poll (%s) not in survey (%s) (kownn: %s)",
						 poll, survey, survey.questions)

	result = QSubmittedSurvey(surveyId=set_submission.surveyId, 
							  questions=submitted)
	return result
