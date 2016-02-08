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

from nti.assessment._util import make_sublocations as _make_sublocations

from nti.assessment.common import QPersistentSubmittable

from nti.assessment.interfaces import ASSIGNMENT_MIME_TYPE
from nti.assessment.interfaces import TIMED_ASSIGNMENT_MIME_TYPE

from nti.assessment.interfaces import IQAssignment
from nti.assessment.interfaces import IQAssignmentPart
from nti.assessment.interfaces import IQBaseSubmission
from nti.assessment.interfaces import IQTimedAssignment
from nti.assessment.interfaces import IQAssignmentSubmissionPendingAssessment

from nti.common.property import alias
from nti.common.property import readproperty

from nti.dataserver_core.interfaces import IContained as INTIContained

from nti.dataserver_core.mixins import ContainedMixin

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.externalization.representation import WithRepr

from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

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
@interface.implementer(IQAssignment, INTIContained)
class QAssignment(QPersistentSubmittable):

	createDirectFieldProperties(IQAssignment)

	title = AdaptingFieldProperty(IQAssignment['title'])

	mimeType = mime_type = ASSIGNMENT_MIME_TYPE

	id = alias('ntiid')

	@readproperty
	def no_submit(self):
		return self.category_name == 'no_submit'

	def iter_question_sets(self):
		for part in self.parts:
			yield part.question_set

	@property
	def containerId(self):
		return 		getattr(self.__parent__, 'ntiid', None) \
				or	getattr(self.__parent__, 'aliasId', None)

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
