#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The assignment related objects.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.cachedescriptors.property import Lazy
from zope.cachedescriptors.property import readproperty

from zope.container.contained import Contained

from zope.location.interfaces import ISublocations

from zope.mimetype.interfaces import IContentTypeAware

from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from persistent import Persistent

from nti.assessment._util import make_sublocations as _make_sublocations

from nti.assessment.common import make_schema
from nti.assessment.common import get_containerId
from nti.assessment.common import compute_part_ntiid

from nti.assessment.common import VersionedMixin
from nti.assessment.common import AssessmentSchemaMixin
from nti.assessment.common import QPersistentSubmittable

from nti.assessment.interfaces import ASSIGNMENT_MIME_TYPE
from nti.assessment.interfaces import TIMED_ASSIGNMENT_MIME_TYPE
from nti.assessment.interfaces import DISCUSSION_ASSIGNMENT_MIME_TYPE

from nti.assessment.interfaces import IQAssignment
from nti.assessment.interfaces import IQAssignmentPart
from nti.assessment.interfaces import IQBaseSubmission
from nti.assessment.interfaces import IQTimedAssignment
from nti.assessment.interfaces import IQDiscussionAssignment
from nti.assessment.interfaces import IQAssignmentSubmissionPendingAssessment

from nti.contentfragments.interfaces import IPlainTextContentFragment

from nti.coremetadata.interfaces import IContained as INTIContained

from nti.coremetadata.mixins import ContainedMixin

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.externalization.representation import WithRepr

from nti.property.property import alias

from nti.schema.eqhash import EqHash

from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


@WithRepr
@EqHash('ntiid')
@interface.implementer(IQAssignmentPart, IContentTypeAware)
class QAssignmentPart(SchemaConfigured,
                      Persistent,
                      Contained):
    createDirectFieldProperties(IQAssignmentPart)

    title = AdaptingFieldProperty(IQAssignmentPart['title'])

    mimeType = mime_type = 'application/vnd.nextthought.assessment.assignmentpart'

    @readproperty
    def ntiid(self):  # pylint: disable=method-hidden
        result = compute_part_ntiid(self)
        if result:
            self.ntiid = result
        return result

    def schema(self):
        result = make_schema(schema=IQAssignmentPart)
        return result


@WithRepr
@interface.implementer(IQAssignment, INTIContained)
class QAssignment(QPersistentSubmittable, AssessmentSchemaMixin):
    createDirectFieldProperties(IQAssignment)

    mimeType = mime_type = ASSIGNMENT_MIME_TYPE

    id = alias('ntiid')

    tags = ()
    parts = ()

    @readproperty
    def no_submit(self):
        return self.category_name == 'no_submit'

    def iter_question_sets(self):
        for part in self.parts or ():
            if part.question_set is not None:
                yield part.question_set

    @readproperty
    def containerId(self):
        return get_containerId(self)

    def __setattr__(self, name, value):
        super(QAssignment, self).__setattr__(name, value)
        if name == "parts":
            for x in self.parts or ():
                x.__parent__ = self  # take ownership


@WithRepr
@interface.implementer(IQTimedAssignment)
class QTimedAssignment(QAssignment):
    createDirectFieldProperties(IQTimedAssignment)

    mimeType = mime_type = TIMED_ASSIGNMENT_MIME_TYPE

    maximum_time_allowed = FP(IQTimedAssignment['maximum_time_allowed'])


@WithRepr
@interface.implementer(IQDiscussionAssignment)
class QDiscussionAssignment(QAssignment):
    createDirectFieldProperties(IQDiscussionAssignment)

    mimeType = mime_type = DISCUSSION_ASSIGNMENT_MIME_TYPE

    @Lazy
    def category_name(self):
        return IPlainTextContentFragment(u'no_submit')


@WithRepr
@interface.implementer(IQAssignmentSubmissionPendingAssessment,
                       IContentTypeAware,
                       IAttributeAnnotatable,
                       ISublocations)
class QAssignmentSubmissionPendingAssessment(ContainedMixin,
                                             SchemaConfigured,
                                             VersionedMixin,
                                             PersistentCreatedModDateTrackingObject):
    createDirectFieldProperties(IQBaseSubmission)
    createDirectFieldProperties(IQAssignmentSubmissionPendingAssessment)

    # We get nti.dataserver.interfaces.IContained from ContainedMixin (containerId, id)
    # However, because these objects are new and not seen before, we can
    # safely cause name and id to be aliases
    __name__ = alias('id')

    mimeType = mime_type = 'application/vnd.nextthought.assessment.assignmentsubmissionpendingassessment'

    __external_can_create__ = False

    sublocations = _make_sublocations()

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
        # schema configured is not cooperative
        ContainedMixin.__init__(self, *args, **kwargs)
        PersistentCreatedModDateTrackingObject.__init__(self)

    @readproperty
    def containerId(self):  # pylint: disable=method-hidden
        return self.assignmentId
