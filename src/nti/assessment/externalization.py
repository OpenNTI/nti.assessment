#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Externalization for assessment objects.

.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.externalization.interfaces import IInternalObjectIO
from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IInternalObjectExternalizer

from nti.externalization.datastructures import InterfaceObjectIO

from .response import QUploadedFile
from .response import QUploadedImageFile

from .interfaces import IQAssessedPart
from .interfaces import IQUploadedFile
from .interfaces import IQSubmittedPart
from .interfaces import IQAssessedQuestion
from .interfaces import IQuestionSubmission
from .interfaces import IQAssessedQuestionSet
from .interfaces import IQuestionSetSubmission

from .interfaces import IQPollSubmission
from .interfaces import IQSurveySubmission

OID = StandardExternalFields.OID
NTIID = StandardExternalFields.NTIID

@interface.implementer(IInternalObjectIO)
class _AssessmentInternalObjectIOBase(object):
	"""
	Base class to customize object IO. See zcml.
	"""

	@classmethod
	def _ap_compute_external_class_name_from_interface_and_instance(cls, iface, impl):
		result = getattr(impl, '__external_class_name__', None)
		if not result:
			# Strip off 'IQ' if it's not 'IQuestionXYZ'
			result = iface.__name__[2:] if not iface.__name__.startswith('IQuestion') \
					 else iface.__name__[1:]
			# Strip NonGradable
			idx = result.find('NonGradable')
			if idx >= 0:
				result = result[0:idx] + result[idx + 11:]
		return result

	@classmethod
	def _ap_compute_external_class_name_from_concrete_class(cls, a_type):
		k = a_type.__name__
		ext_class_name = k[1:] if not k.startswith('Question') else k
		return ext_class_name

@interface.implementer(IInternalObjectExternalizer)
class _QContainedObjectExternalizer(object):

	interface = None

	def __init__(self, item):
		self.item = item

	def toExternalObject(self, **kwargs):
		if hasattr(self.item, 'sublocations'):
			# sets the full parent lineage for these objects.
			# we wrapp the execution of it in a tuple in case it
			# returns a generator
			tuple(self.item.sublocations())
		return InterfaceObjectIO(self.item, self.interface).toExternalObject(**kwargs)

@component.adapter(IQSubmittedPart)
class _QSubmittedPartExternalizer(_QContainedObjectExternalizer):
	interface = IQSubmittedPart

@component.adapter(IQAssessedPart)
class _QAssessedPartExternalizer(_QContainedObjectExternalizer):
	interface = IQAssessedPart

@component.adapter(IQuestionSubmission)
class _QuestionSubmissionExternalizer(_QContainedObjectExternalizer):
	interface = IQuestionSubmission

@component.adapter(IQuestionSetSubmission)
class _QuestionSetSubmissionExternalizer(_QContainedObjectExternalizer):
	interface = IQuestionSetSubmission

@component.adapter(IQAssessedQuestion)
class _QAssessedQuestionExternalizer(_QContainedObjectExternalizer):
	interface = IQAssessedQuestion

@component.adapter(IQAssessedQuestionSet)
class _QAssessedQuestionSetExternalizer(_QContainedObjectExternalizer):
	interface = IQAssessedQuestionSet

@component.adapter(IQPollSubmission)
class _QPollSubmissionExternalizer(_QContainedObjectExternalizer):
	interface = IQPollSubmission

@component.adapter(IQSurveySubmission)
class _QSurveySubmissionSubmissionExternalizer(_QContainedObjectExternalizer):
	interface = IQSurveySubmission

# File uploads

from nti.namedfile.datastructures import BaseFactory
from nti.namedfile.datastructures import NamedFileObjectIO

@component.adapter(IQUploadedFile)
class _QUploadedFileObjectIO(NamedFileObjectIO):

	_excluded_in_ivars_ = {'download_url', 'url', 'value'}.union(NamedFileObjectIO._excluded_in_ivars_)

	def _ext_mimeType(self, obj):
		return u'application/vnd.nextthought.assessment.uploadedfile'

	def toExternalObject(self, mergeFrom=None, **kwargs):
		ext_dict = super(_QUploadedFileObjectIO, self).toExternalObject(**kwargs)
		return ext_dict

def _QUploadedFileFactory(ext_obj):
	factory = BaseFactory(ext_obj, QUploadedFile, QUploadedImageFile)
	return factory
