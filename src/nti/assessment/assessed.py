#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Having to do with submitting external data for grading.

.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time

from zope import interface
from zope import component

from zope.location.interfaces import ISublocations

from persistent import Persistent
from persistent.list import PersistentList

from nti.coremetadata.interfaces import ICreated
from nti.coremetadata.interfaces import ILastModified

from nti.dataserver_core.mixins import ContainedMixin

from nti.externalization.representation import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import InvalidValue
from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from .interfaces import IQuestion
from .interfaces import IQuestionSet
from .interfaces import IQAssessedPart
from .interfaces import IQAssessedQuestion
from .interfaces import IQuestionSubmission
from .interfaces import IQAssessedQuestionSet

from ._util import make_sublocations as _make_sublocations
from ._util import dctimes_property_fallback as _dctimes_property_fallback

from .common import QSubmittedPart

@interface.implementer(IQAssessedPart, ISublocations)
@EqHash('assessedValue', 'submittedResponse',
		superhash=True)
@WithRepr
class QAssessedPart(QSubmittedPart):
	createDirectFieldProperties(IQAssessedPart)

@interface.implementer(IQAssessedQuestion,
					   ICreated,
					   ILastModified,
					   ISublocations)
@EqHash('questionId', 'parts',
		superhash=True)
@WithRepr
class QAssessedQuestion(SchemaConfigured,
						ContainedMixin,
						Persistent):
	createDirectFieldProperties(IQAssessedQuestion)

	__external_can_create__ = False

	creator = None
	createdTime = _dctimes_property_fallback('createdTime', 'Date.Modified')
	lastModified = _dctimes_property_fallback('lastModified', 'Date.Created')

	def __init__(self, *args, **kwargs):
		super(QAssessedQuestion, self).__init__(*args, **kwargs)
		self.lastModified = self.createdTime = time.time()

	def updateLastMod(self, t=None):
		self.lastModified = (t if t is not None and t > self.lastModified else time.time())
		return self.lastModified

	sublocations = _make_sublocations()

@interface.implementer(IQAssessedQuestionSet,
					   ICreated,
					   ILastModified)
@EqHash('questionSetId', 'questions',
		superhash=True)
@WithRepr
class QAssessedQuestionSet(SchemaConfigured,
						   ContainedMixin,
						   Persistent):

	createDirectFieldProperties(IQAssessedQuestionSet)
	__external_can_create__ = False

	creator = None
	createdTime = _dctimes_property_fallback('createdTime', 'Date.Modified')
	lastModified = _dctimes_property_fallback('lastModified', 'Date.Created')

	def __init__(self, *args, **kwargs):
		super(QAssessedQuestionSet, self).__init__(*args, **kwargs)
		self.lastModified = self.createdTime = time.time()

	def updateLastMod(self, t=None):
		self.lastModified = (t if t is not None and t > self.lastModified else time.time())
		return self.lastModified

	sublocations = _make_sublocations('questions')

def assess_question_submission(submission, registry=component):
	"""
	Assess the given question submission.

	:return: An :class:`.interfaces.IQAssessedQuestion`.
	:param submission: An :class:`.interfaces.IQuestionSubmission`.
		The ``parts`` of this submission must be the same length
		as the parts of the question being submitted. If there is no
		answer to a part, then the corresponding value in the submission
		array should be ``None`` and the auto-assessment will be 0.0.
		(In the future, if we have questions
		with required and/or optional parts, we would implement that check
		here).
	:param registry: If given, an :class:`.IComponents`. If
		not given, the current component registry will be used.
		Used to look up the question set and question by id.
	:raises LookupError: If no question can be found for the submission.
	:raises Invalid: If a submitted part has the wrong kind of input
		to be graded.
	"""

	question = registry.getUtility(IQuestion, name=submission.questionId)
	if len(question.parts) != len(submission.parts):
		raise ValueError("Question (%s) and submission (%s) have different numbers of parts." %
						 (len(question.parts), len(submission.parts)))

	assessed_parts = PersistentList()

	for sub_part, q_part in zip(submission.parts, question.parts):
		# Grade what they submitted, if they submitted something. If they didn't
		# submit anything, it's automatically "wrong."
		try:
			grade = q_part.grade(sub_part) if sub_part is not None else 0.0
		except (LookupError, ValueError):
			# We couldn't grade the part because the submission was in the wrong
			# format. Translate this error to something more useful.
			__traceback_info__ = sub_part, q_part
			raise InvalidValue(value=sub_part, field=IQuestionSubmission['parts'])
		else:
			apart = QAssessedPart(submittedResponse=sub_part, assessedValue=grade)
			assessed_parts.append(apart)

	result = QAssessedQuestion(questionId=submission.questionId, parts=assessed_parts)
	return result

def assess_question_set_submission(set_submission, registry=component):
	"""
	Assess the given question set submission.

	:return: An :class:`.interfaces.IQAssessedQuestionSet`.
	:param set_submission: An :class:`.interfaces.IQuestionSetSubmission`.
	:param registry: If given, an :class:`.IComponents`. If
		not given, the current component registry will be used.
		Used to look up the question set and question by id.
	:raises LookupError: If no question can be found for the submission.
	"""
	question_set = registry.getUtility(IQuestionSet, name=set_submission.questionSetId)
	questions_ntiids = {q.ntiid for q in question_set.questions}

	# NOTE: At this point we need to decide what to do for missing values
	# We are currently not really grading them at all, which is what we
	# did for the old legacy quiz stuff

	assessed = PersistentList()
	for sub_question in set_submission.questions:
		question = registry.getUtility( IQuestion, name=sub_question.questionId )
		if 	question in question_set.questions or question.ntiid in questions_ntiids:
			sub_assessed = IQAssessedQuestion(sub_question)  # Raises ComponentLookupError
			assessed.append(sub_assessed)
		else: # pragma: no cover
			logger.debug("Bad input, question (%s) not in question set (%s) (known: %s)",
						 question, question_set, question_set.questions)

	# NOTE: We're not really creating some sort of aggregate grade here
	result = QAssessedQuestionSet(questionSetId=set_submission.questionSetId,
								  questions=assessed)
	return result
