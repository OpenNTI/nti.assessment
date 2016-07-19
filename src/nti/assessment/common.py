#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time
import hashlib
from datetime import datetime
from collections import Mapping

import isodate

import simplejson as json

from zope import component
from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.container.contained import Contained

from zope.location.interfaces import ISublocations

from zope.mimetype.interfaces import IContentTypeAware

from persistent import Persistent

from nti.assessment import ASSESSMENT_INTERFACES

from nti.assessment.interfaces import PART_NTIID_TYPE

from nti.assessment.interfaces import IQPart
from nti.assessment.interfaces import IQAssessment
from nti.assessment.interfaces import IQAssignment
from nti.assessment.interfaces import IQSubmittable
from nti.assessment.interfaces import IQSubmittedPart
from nti.assessment.interfaces import IQNonGradablePart
from nti.assessment.interfaces import IQEditableEvaluation
from nti.assessment.interfaces import IQPartResponseNormalizer
from nti.assessment.interfaces import IQAssessmentJsonSchemaMaker
from nti.assessment.interfaces import IQLatexSymbolicMathSolution
from nti.assessment.interfaces import IQEvaluationContainerIdGetter

from nti.assessment.randomized.interfaces import IQRandomizedPart

from nti.common.property import alias

from nti.coremetadata.mixins import RecordableMixin
from nti.coremetadata.mixins import CalendarPublishableMixin

from nti.coremetadata.utils import make_schema

from nti.coremetadata.interfaces import SYSTEM_USER_ID

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.dublincore.time_mixins import CreatedAndModifiedTimeMixin

from nti.externalization.externalization import toExternalObject

from nti.externalization.oids import to_external_oid

from nti.externalization.representation import WithRepr

from nti.ntiids.ntiids import get_parts
from nti.ntiids.ntiids import make_ntiid
from nti.ntiids.ntiids import make_specific_safe

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.interfaces import find_most_derived_interface

from nti.schema.schema import EqHash

# functions

def grade_one_response(questionResponse, possible_answers):
	"""
	:param questionResponse: The string to evaluate. It may be in latex notation
		or openmath XML notation, or plain text. We may edit the response
		to get something parseable.
	:param list possible_answers: A sequence of possible answers to compare
		`questionResponse` with.
	"""

	match = False
	answers = [IQLatexSymbolicMathSolution(t) for t in possible_answers]
	for answer in answers:
		match = answer.grade(questionResponse)
		if match:
			return match
	return False

def assess(quiz, responses):
	result = {}
	for questionId, questionResponse in responses.iteritems():
		answers = quiz[questionId].answers
		result[questionId] = grade_one_response(questionResponse, answers)
	return result

def grader_for_solution_and_response(part, solution, response, creator=None):
	result = None
	if 		(part.randomized or IQRandomizedPart.providedBy( part )) \
		and part.randomized_grader_interface:
		grader_interface = part.randomized_grader_interface

		# Only randomized graders care about creators; do this here so
		# we do not accidentally get randomized graders unintentionally.
		result = component.queryMultiAdapter((part, solution, response, creator),
										  	grader_interface,
										  	name=part.grader_name)
	else:
		grader_interface = part.grader_interface

	if result is None:
		result = component.queryMultiAdapter((part, solution, response),
										  	grader_interface,
										  	name=part.grader_name)
	return result
grader = grader_for_solution_and_response  # alias BWC

def grader_for_response(part, response):
	for solution in part.solutions or ():
		grader = grader_for_solution_and_response(part, solution, response)
		if grader is not None:
			return grader
	return None

def normalize_response(part, response):
	normalizer = component.queryMultiAdapter((part, response),
										 	 IQPartResponseNormalizer)
	result = normalizer()
	return result

def hexdigest(data, hasher=None):
	hasher = hashlib.sha256() if hasher is None else hasher
	hasher.update(data)
	result = hasher.hexdigest()
	return result

def signature(data, decorate=False):
	if not isinstance(data, Mapping):
		data = toExternalObject(data, decorate=decorate)
	result = hexdigest(json.dumps(data, sort_keys=True))
	return result

def hashfile(afile, hasher=None, blocksize=65536):
	hasher = hashlib.sha256() if hasher is None else hasher
	buf = afile.read(blocksize)
	while len(buf) > 0:
		hasher.update(buf)
		buf = afile.read(blocksize)
	return hasher.hexdigest()

def iface_of_assessment(thing):
	for iface in ASSESSMENT_INTERFACES:
		if iface.providedBy(thing):
			return iface
	for iface in (IQPart, IQNonGradablePart):
		if iface.providedBy(thing):
			return iface
	return None

def get_containerId(item):
	getter = component.queryUtility(IQEvaluationContainerIdGetter)
	if getter is not None:
		result = getter(item)
	else:
		for name in ('__home__', '__parent__'):
			attribute = getattr(item, name, None)
			result = getattr(attribute, 'ntiid', None)
			if result:
				break
	return result

def compute_part_ntiid(part):
	parent = part.__parent__
	parent_parts = getattr(parent, 'parts', ())
	base_ntiid = getattr(parent, 'ntiid', None)
	if base_ntiid and parent_parts:
		# Gather all child parts ntiids.
		parent_part_ids = set()
		for child_part in parent_parts or ():
			child_part_ntiid = child_part.__dict__.get( 'ntiid' )
			parent_part_ids.add(child_part_ntiid)
		parent_part_ids.discard(None)

		# Get initial part unique id
		uid = to_external_oid(part) if IQEditableEvaluation.providedBy(parent) else None
		uid = make_specific_safe(uid or str(0))  # legacy
		parts = get_parts(base_ntiid)

		idx = 0
		# Iterate until we find an ntiid that does not collide.
		while True:
			specific = "%s.%s" % (parts.specific, uid)
			result = make_ntiid(parts.date,
								parts.provider,
								PART_NTIID_TYPE,
								specific)
			if result not in parent_part_ids:
				break
			idx += 1
			uid = idx
		return result
	return None

# classes

class VersionedMixin(object):

	version = None  # Default to None
	Version = alias('version')

	def __init__(self, *args, **kwargs):
		super(VersionedMixin, self).__init__(*args, **kwargs)

	def _get_version_timestamp(self):
		value = datetime.fromtimestamp(time.time())
		return unicode(isodate.datetime_isoformat(value))

	def update_version(self, version=None):
		self.version = version if version else self._get_version_timestamp()
		return self.version

@WithRepr
@interface.implementer(IQSubmittable, IContentTypeAware, IAttributeAnnotatable)
class QSubmittable(SchemaConfigured,
				   VersionedMixin,
				   RecordableMixin,
				   CalendarPublishableMixin,
				   CreatedAndModifiedTimeMixin,
				   Contained):

	ntiid = None

	available_for_submission_ending = AdaptingFieldProperty(IQAssignment['available_for_submission_ending'])
	available_for_submission_beginning = AdaptingFieldProperty(IQAssignment['available_for_submission_beginning'])

	not_after = alias('available_for_submission_ending')
	not_before = alias('available_for_submission_beginning')

	parameters = {}  # IContentTypeAware

	def __init__(self, *args, **kwargs):
		SchemaConfigured.__init__(self, *args, **kwargs)

class QPersistentSubmittable(QSubmittable, PersistentCreatedModDateTrackingObject):

	createdTime = 0
	creator = SYSTEM_USER_ID

	def __init__(self, *args, **kwargs):
		# schema configured is not cooperative
		QSubmittable.__init__(self, *args, **kwargs)
		PersistentCreatedModDateTrackingObject.__init__(self)

@WithRepr
@EqHash('submittedResponse', superhash=True)
@interface.implementer(IQSubmittedPart, ISublocations)
class QSubmittedPart(SchemaConfigured, Persistent, Contained):

	submittedResponse = None

	__external_can_create__ = False

	createDirectFieldProperties(IQSubmittedPart)

	def sublocations(self):
		part = self.submittedResponse
		if hasattr(part, '__parent__'):  # take ownership
			if part.__parent__ is None:
				part.__parent__ = self
			if part.__parent__ is self:
				yield part

# schema

class EvaluationSchemaMixin(object):
	"""
	Mixin to pull a schema for a given implementation.
	"""

	def schema(self, user=None):
		schema = find_most_derived_interface(self, IQAssessment)
		result = make_schema(schema=schema, user=None, maker=IQAssessmentJsonSchemaMaker)
		return result
AssessmentSchemaMixin = EvaluationSchemaMixin
