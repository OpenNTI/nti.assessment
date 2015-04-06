#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
from nti.assessment.interfaces import IQResponse
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

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
from persistent.mapping import PersistentMapping

from nti.common.property import alias

from nti.dataserver.core.mixins import ContainedMixin

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.externalization.representation import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from ._util import make_sublocations as _make_sublocations

from .common import normalize_response

from .interfaces import IQPoll
from .interfaces import IQSurvey
from .interfaces import IQBaseSubmission
from .interfaces import IQPollSubmission
from .interfaces import IQSurveySubmission

from .interfaces import IQNonGradableFreeResponsePart
from .interfaces import IQNonGradableModeledContentPart
from .interfaces import IQNonGradableMultipleChoicePart
from .interfaces import IQNonGradableMultipleChoiceMultipleAnswerPart

from .interfaces import IQAggregatedPart
from .interfaces import IQAggregatedPoll
from .interfaces import IQAggregatedSurvey
from .interfaces import IQAggregatedFreeResponsePart
from .interfaces import IQAggregatedModeledContentPart
from .interfaces import IQAggregatedMultipleChoicePart
from .interfaces import IQAggregatedMultipleChoiceMultipleAnswerPart

from .interfaces import SURVEY_MIME_TYPE

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
	polls = parts = alias('questions')

	createDirectFieldProperties(IQSurvey)

	title = AdaptingFieldProperty(IQSurvey['title'])

	mimeType = mime_type = SURVEY_MIME_TYPE

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

	def __iter__(self):
		return iter(self.parts)

	def __getitem__(self, idx):
		return self.parts[idx]

	def __setitem__(self, idx, value):
		self.parts[idx] = value
		
	def __delitem__(self, idx):
		del self.parts[idx]
	
	def __len__(self):
		return len(self.parts)
	
@WithRepr
@interface.implementer(IWriteMapping)
class QBasePollSet(object):
	
	def get(self, key, default=None):
		try:
			return self[key]
		except KeyError:
			return default
		
	def index(self, key):
		for idx, poll in enumerate(self.polls or ()):
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

@interface.implementer(IQSurveySubmission, ISublocations)
class QSurveySubmission(ContainedMixin,
					    SchemaConfigured,
					    PersistentCreatedModDateTrackingObject,
					    QBasePollSet):
	createDirectFieldProperties(IQBaseSubmission)
	createDirectFieldProperties(IQSurveySubmission)

	parts = polls = alias('questions')

	sublocations = _make_sublocations('questions')
	
	def __init__(self, *args, **kwargs):
		# schema configured is not cooperative
		ContainedMixin.__init__(self, *args, **kwargs)
		PersistentCreatedModDateTrackingObject.__init__(self)

## Aggregation

@WithRepr
@interface.implementer(IQAggregatedPart)
class QAggregatedPart(ContainedMixin,
					  SchemaConfigured,
					  PersistentCreatedModDateTrackingObject):
	
	createDirectFieldProperties(IQAggregatedPart)
	
	results = None
	
	__external_can_create__ = False
	
	def __init__(self, *args, **kwargs):
		# schema configured is not cooperative
		ContainedMixin.__init__(self, *args, **kwargs)
		PersistentCreatedModDateTrackingObject.__init__(self)
		self.reset()

	def reset(self):
		raise NotImplementedError()

	def append(self, response):
		raise NotImplementedError()

@interface.implementer(IQAggregatedMultipleChoicePart)
class QAggregatedMultipleChoicePart(QAggregatedPart):
	createDirectFieldProperties(IQAggregatedMultipleChoicePart)
	
	def Results(self):
		return dict(self.results)

	def reset(self):
		self.results = PersistentMapping()
		
	def append(self, response):
		current = self.result.get(response) or 0
		self.results[response] = current + 1

	def __iadd__(self, other):
		assert IQAggregatedMultipleChoicePart.providedBy(other)
		for k, v in other.results.items():
			current = v + self.result.get(k) or 0
			self.result[k] = current
		return self

@interface.implementer(IQAggregatedMultipleChoiceMultipleAnswerPart)
class QMultipleChoiceMultipleAnswerAggregatedPart(QAggregatedMultipleChoicePart):
	createDirectFieldProperties(IQAggregatedMultipleChoiceMultipleAnswerPart)
	
@interface.implementer(IQAggregatedFreeResponsePart)
class QAggregatedFreeResponsePart(QAggregatedPart):
	createDirectFieldProperties(IQAggregatedFreeResponsePart)
	
	def Results(self):
		return dict(self.results)
	
	def reset(self):
		self.results = PersistentMapping()
		
	def append(self, response):
		current = self.result.get(response) or 0
		self.results[response] = current + 1

	def __iadd__(self, other):
		assert IQAggregatedFreeResponsePart.providedBy(other)
		for k, v in other.results.items():
			current = v + self.result.get(k) or 0
			self.result[k] = current
		return self

@interface.implementer(IQAggregatedModeledContentPart)
class QAggregatedModeledContentPart(QAggregatedPart):
	createDirectFieldProperties(IQAggregatedModeledContentPart)
	
	def Results(self):
		return list(self.results)
	
	def reset(self):
		self.results = PersistentList()
		
	def append(self, response):
		self.results.append(response)
	
	def __iadd__(self, other):
		assert IQAggregatedModeledContentPart.providedBy(other)
		self.results.extend(other.results)
		return self

@WithRepr
@interface.implementer(IQAggregatedPoll, ISublocations, IFiniteSequence)
class QAggregatedPoll(ContainedMixin,
					  SchemaConfigured,
					  PersistentCreatedModDateTrackingObject):
	
	createDirectFieldProperties(IQAggregatedPoll)
	
	sublocations = _make_sublocations()
	
	def __init__(self, *args, **kwargs):
		# schema configured is not cooperative
		ContainedMixin.__init__(self, *args, **kwargs)
		PersistentCreatedModDateTrackingObject.__init__(self)
	
	def __iter__(self):
		return iter(self.parts)

	def __getitem__(self, idx):
		return self.parts[idx]

	def __setitem__(self, idx, value):
		self.parts[idx] = value
		
	def __delitem__(self, idx):
		del self.parts[idx]
	
	def __len__(self):
		return len(self.parts)

@interface.implementer(IQAggregatedSurvey, ISublocations, IWriteMapping)
class QAggregatedSurvey(ContainedMixin,
					  	SchemaConfigured,
					  	PersistentCreatedModDateTrackingObject,
					  	QBasePollSet):
	
	createDirectFieldProperties(IQAggregatedSurvey)
		
	parts = polls = alias('questions')
	
	sublocations = _make_sublocations('questions')
		
	def __init__(self, *args, **kwargs):
		# schema configured is not cooperative
		ContainedMixin.__init__(self, *args, **kwargs)
		PersistentCreatedModDateTrackingObject.__init__(self)

def aggregated_part_factory(part):
	if IQNonGradableFreeResponsePart.providedBy(part):
		return QAggregatedFreeResponsePart
	elif IQNonGradableModeledContentPart.providedBy(part):
		return QAggregatedModeledContentPart
	elif IQNonGradableMultipleChoicePart.providedBy(part):
		return QAggregatedMultipleChoicePart
	elif IQNonGradableMultipleChoiceMultipleAnswerPart.providedBy(part):
		return QMultipleChoiceMultipleAnswerAggregatedPart
	raise TypeError("Cannot find aggregated part factory for %s", part)

def aggregate_poll_submission(submission, registry=component):
	"""
	aggregte the given poll submission.

	:return: An :class:`.interfaces.IQAggregatedPoll`.
	:param submission: An :class:`.interfaces.IQPollSubmission`.
		The ``parts`` of this submission must be the same length
		as the parts of the poll being submitted. 
	:param registry: If given, an :class:`.IComponents`. If
		not given, the current component registry will be used.
		Used to look up the poll by id.
	:raises LookupError: If no poll can be found for the submission.
	:raises Invalid: If a submitted part has the wrong kind of input
	"""

	pollId = submission.pollId
	poll = registry.getUtility(IQPoll, name=pollId)
	if len(poll.parts) != len(submission.parts):
		raise ValueError("Poll (%s) and submission (%s) have different numbers of parts." %
						 (len(poll.parts), len(submission.parts)))

	aggregated_parts = PersistentList()	
	for sub_part, q_part in zip(submission.parts, poll.parts):
		__traceback_info__ = sub_part, q_part
		response = IQResponse(sub_part)
		response = normalize_response(response, q_part)
		aggregated_part = aggregated_part_factory(q_part)()
		aggregated_part.append(response)
		aggregated_parts.append(aggregated_part)
		
	aggregated = QAggregatedPoll(pollId=pollId, parts=aggregated_parts)
	return aggregated

def aggregate_survey_submission(submission, registry=component):
	"""
	Assess the given survey submission.

	:return: An :class:`.interfaces.IQAggregatedSurvey`.
	:param submission: An :class:`.interfaces.IQSurveySubmission`.
	:param registry: If given, an :class:`.IComponents`. If
		not given, the current component registry will be used.
		Used to look up the survey and pools by id.
	:raises LookupError: If no poll/survey can be found for the submission.
	"""
	survey = registry.getUtility(IQSurvey, name=submission.surveyId)
	poll_ntiids = {q.ntiid for q in survey.questions}

	assessed = PersistentList()
	for sub_poll in submission.questions:
		poll = registry.getUtility(IQPoll, name=sub_poll.pollId )
		if poll.ntiid in poll_ntiids or poll in survey.questions:
			sub_aggregated = IQAggregatedPoll(sub_poll)
			assessed.append(sub_aggregated)
		else: # pragma: no cover
			logger.debug("Bad input, poll (%s) not in survey (%s) (kownn: %s)",
						 poll, survey, survey.questions)

	result = QAggregatedSurvey(surveyId=survey.surveyId, questions=assessed)
	return result