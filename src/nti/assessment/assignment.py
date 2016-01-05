#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The assignment related objects.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.container.contained import Contained

from zope.location.interfaces import ISublocations

from zope.mimetype.interfaces import IContentTypeAware

from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from persistent import Persistent

from nti.common.property import alias, readproperty

from nti.dataserver_core.mixins import ContainedMixin

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.externalization.representation import WithRepr

from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from ._util import make_sublocations as _make_sublocations

from .common import QPersistentSubmittable

from .interfaces import ASSIGNMENT_MIME_TYPE
from .interfaces import TIMED_ASSIGNMENT_MIME_TYPE

from .interfaces import IQAssignment
from .interfaces import IQAssignmentPart
from .interfaces import IQBaseSubmission
from .interfaces import IQTimedAssignment
from .interfaces import IQAssignmentSubmissionPendingAssessment

@WithRepr
@interface.implementer(IQAssignmentPart,
					   IContentTypeAware)
class QAssignmentPart(SchemaConfigured,
					  Contained,
					  Persistent):
	createDirectFieldProperties(IQAssignmentPart)

	title = AdaptingFieldProperty(IQAssignmentPart['title'])
	
	mimeType = mime_type = 'application/vnd.nextthought.assessment.assignmentpart'

@WithRepr
@interface.implementer(IQAssignment)
class QAssignment(QPersistentSubmittable):

	createDirectFieldProperties(IQAssignment)

	title = AdaptingFieldProperty(IQAssignment['title'])
	
	mimeType = mime_type = ASSIGNMENT_MIME_TYPE
	
	@readproperty
	def no_submit(self):
		return self.category_name == 'no_submit'
	
	def iter_question_sets(self):
		for part in self.parts:
			yield part.question_set

@WithRepr
@interface.implementer(IQTimedAssignment)
class QTimedAssignment(QAssignment):
	createDirectFieldProperties(IQTimedAssignment)
	
	maximum_time_allowed = FP(IQTimedAssignment['maximum_time_allowed'])
	
	mimeType = mime_type = TIMED_ASSIGNMENT_MIME_TYPE

@WithRepr
@interface.implementer(IQAssignmentSubmissionPendingAssessment,
					   IContentTypeAware,
					   IAttributeAnnotatable,
					   ISublocations)
class QAssignmentSubmissionPendingAssessment(ContainedMixin,
											 SchemaConfigured,
											 PersistentCreatedModDateTrackingObject):
	createDirectFieldProperties(IQBaseSubmission)
	createDirectFieldProperties(IQAssignmentSubmissionPendingAssessment)
	
	# We get nti.dataserver.interfaces.IContained from ContainedMixin (containerId, id)
	# However, because these objects are new and not seen before, we can
	# safely cause name and id to be aliases
	__name__ = alias('id')

	mime_type = 'application/vnd.nextthought.assessment.assignmentsubmissionpendingassessment'
	
	__external_can_create__ = False

	sublocations = _make_sublocations()

	def __init__(self, *args, **kwargs):
		# schema configured is not cooperative
		ContainedMixin.__init__(self, *args, **kwargs)
		PersistentCreatedModDateTrackingObject.__init__(self)
