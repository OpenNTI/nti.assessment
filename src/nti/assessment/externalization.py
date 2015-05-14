#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Externalization for assessment objects.

.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope import component

from zope.file.upload import nameFinder

from nti.common.dataurl import DataURL

from nti.links.links import Link

from nti.coremetadata.schema import DataURI

from nti.dataserver.core.interfaces import ILinkExternalHrefOnly

from nti.externalization.interfaces import IInternalObjectIO
from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IInternalObjectExternalizer

from nti.externalization.externalization import to_external_object
from nti.externalization.externalization import to_external_ntiid_oid

from nti.externalization.datastructures import InterfaceObjectIO
from nti.externalization.datastructures import AbstractDynamicObjectIO

from .response import QUploadedFile
from .response import QUploadedImageFile

from .interfaces import IQAssessedPart
from .interfaces import IQUploadedFile
from .interfaces import IQSubmittedPart
from .interfaces import IQAssessedQuestion
from .interfaces import IQuestionSubmission
from .interfaces import IQAssessedQuestionSet
from .interfaces import IQuestionSetSubmission
from .interfaces import IInternalUploadedFileRef

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
			if idx >=0:
				result = result[0:idx] + result[idx+11:]
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
			## sets the full parent lineage for these objects. 
			## we wrapp the execution of it in a tuple in case it
			## returns a generator
			tuple(self.item.sublocations())
		return InterfaceObjectIO(self.item, self.interface).toExternalObject( **kwargs)

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

##
# File uploads
# TODO: This can probably be generalized.
# We do want to have specific interfaces for files
# submitted for assessment reasons.
##

@component.adapter(IQUploadedFile)
class _QUploadedFileObjectIO(AbstractDynamicObjectIO):

	def __init__( self, ext_self ):
		super(_QUploadedFileObjectIO,self).__init__()
		self._ext_self = ext_self

	def _ext_replacement(self):
		return self._ext_self

	def _ext_all_possible_keys(self):
		return ()

	# For symmetry with the other response types,
	# we accept either 'url' or 'value'

	def updateFromExternalObject( self, parsed, *args, **kwargs ):
		ext_self = self._ext_replacement()
		if parsed.get('download_url') or parsed.get(OID) or parsed.get(NTIID):
			## when updating from an external source and either download_url or 
			## NTIID/OID is provided save the reference
			interface.alsoProvides(ext_self, IInternalUploadedFileRef)
			ext_self.reference = parsed.get(OID) or parsed.get(NTIID)
			## then remove those fields to avoid any hint of a copy
			for name in (OID, NTIID, 'download_url', 'url', 'value', 'filename'):
				parsed.pop(name, None)
		## start update
		updated = super(_QUploadedFileObjectIO, self).updateFromExternalObject(parsed, *args, **kwargs)
		ext_self = self._ext_replacement()
		url = parsed.get('url') or parsed.get('value')
		name = parsed.get('name') or parsed.get('Name')
		if url:
			data_url = DataURI(__name__='url').fromUnicode( url )
			ext_self.contentType = data_url.mimeType
			ext_self.data = data_url.data
			updated = True
		if 'filename' in parsed:
			ext_self.filename = parsed['filename']
			# some times we get full paths
			name_found = nameFinder( ext_self )
			if name_found:
				ext_self.filename = name_found
			name = ext_self.filename if not name else name
			updated = True
		if 'FileMimeType' in parsed:
			ext_self.contentType = bytes(parsed['FileMimeType'])
			updated = True
		if name is not None:
			ext_self.name = name
		return updated

	def toExternalObject( self, mergeFrom=None, **kwargs ):
		ext_dict = super(_QUploadedFileObjectIO,self).toExternalObject(**kwargs)
		## TODO: View name. Coupled to the app layer. And this is now in three places.
		## It's not quite possible to fully traverse to the file sometimes
		## (TODO: verify this in this case) so we go directly to the file address
		the_file = self._ext_replacement()
		ext_dict['name'] = the_file.name or None
		ext_dict['filename'] = the_file.filename or None
		ext_dict['FileMimeType'] = the_file.mimeType or None
		ext_dict['MimeType'] = 'application/vnd.nextthought.assessment.uploadedfile'
		target = to_external_ntiid_oid(the_file, add_to_connection=True)
		if target:
			for element, key in ('view','url'), ('download','download_url'):
				link = Link( target=target,
							 target_mime_type=the_file.contentType,
							 elements=(element,),
							 rel="data" )
				interface.alsoProvides( link, ILinkExternalHrefOnly )
				ext_dict[key] = to_external_object( link )
		else:
			ext_dict['url'] = None
			ext_dict['download_url'] = None
		ext_dict['value'] = ext_dict['url']
		return ext_dict

def _QUploadedFileFactory(ext_obj):
	factory = QUploadedFile
	url = ext_obj.get('url') or ext_obj.get('value')
	contentType = ext_obj.get('FileMimeType')
	if url and url.startswith(b'data:'):
		ext_obj['url'] = DataURL(url)
		ext_obj.pop('value', None)
		if ext_obj['url'].mimeType.startswith('image/'):
			factory = QUploadedImageFile
	elif contentType and contentType.lower().startswith('image/'):
		factory = QUploadedImageFile
	return factory
