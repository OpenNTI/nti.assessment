#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.assessment import FIELDS
from nti.assessment import ACCEPTS

from nti.assessment.common import make_schema

from nti.assessment.interfaces import IQuestion
from nti.assessment.interfaces import IQuestionSet
from nti.assessment.interfaces import IQAssignment
from nti.assessment.interfaces import IQAssessment
from nti.assessment.interfaces import IQAssignmentPart
from nti.assessment.interfaces import IQAssessmentJsonSchemaMaker

from nti.coremetadata.jsonschema import CoreJsonSchemafier

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

ITEMS = StandardExternalFields.ITEMS

class BaseJsonSchemafier(CoreJsonSchemafier):

	def post_process_field(self, name, field, item_schema):
		super(BaseJsonSchemafier, self).post_process_field(name, field, item_schema)

@interface.implementer(IQAssessmentJsonSchemaMaker)
class AssessmentJsonSchemaMaker(object):

	maker = BaseJsonSchemafier

	def make_schema(self, schema=IQAssessment):
		result = LocatedExternalDict()
		maker = self.maker(schema)
		result[FIELDS] = maker.make_schema()
		return result

@interface.implementer(IQAssessmentJsonSchemaMaker)
class ItemContainerJsonSchemaMaker(AssessmentJsonSchemaMaker):

	has_items = True
	ref_interfaces = ()

	def make_schema(self, schema=IQAssessment):
		result = super(ItemContainerJsonSchemaMaker, self).make_schema(schema)
		accepts = result[ACCEPTS] = {}
		for iface in self.ref_interfaces:
			mimeType = iface.getTaggedValue('_ext_mime_type')
			accepts[mimeType] = make_schema(schema=iface).get(FIELDS)
		if self.has_items:
			fields = result[FIELDS]
			base_types = sorted(accepts.keys())
			fields[ITEMS]['base_type'] = base_types if len(base_types) > 1 else base_types[0]
		return result

@interface.implementer(IQAssessmentJsonSchemaMaker)
class AssignmentJsonSchemaMaker(ItemContainerJsonSchemaMaker):

	has_items = False
	ref_interfaces = (IQAssignmentPart,)

	def make_schema(self, schema=IQAssignment):
		result = super(AssignmentJsonSchemaMaker, self).make_schema(schema)
		return result

@interface.implementer(IQAssessmentJsonSchemaMaker)
class AssignmentPartJsonSchemaMaker(ItemContainerJsonSchemaMaker):

	has_items = False
	ref_interfaces = (IQuestionSet,)

	def make_schema(self, schema=IQAssignmentPart):
		result = super(AssignmentPartJsonSchemaMaker, self).make_schema(schema)
		return result

@interface.implementer(IQAssessmentJsonSchemaMaker)
class QuestionSetJsonSchemaMaker(ItemContainerJsonSchemaMaker):

	has_items = False
	ref_interfaces = (IQuestion,)

	def make_schema(self, schema=IQuestionSet):
		result = super(QuestionSetJsonSchemaMaker, self).make_schema(schema)
		return result

@interface.implementer(IQAssessmentJsonSchemaMaker)
class QuestionJsonSchemaMaker(ItemContainerJsonSchemaMaker):

	has_items = False

	def make_schema(self, schema=IQuestion):
		result = super(QuestionJsonSchemaMaker, self).make_schema(schema)
		return result
