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

from nti.dataserver.links import Link
from nti.dataserver.interfaces import ILinkExternalHrefOnly

from nti.externalization.interfaces import IInternalObjectIO
from nti.externalization.datastructures import InterfaceObjectIO
from nti.externalization.externalization import to_external_object
from nti.externalization.externalization import to_external_ntiid_oid
from nti.externalization.interfaces import IInternalObjectExternalizer
from nti.externalization.datastructures import AbstractDynamicObjectIO

from nti.utils.schema import DataURI
from nti.utils.dataurl import DataURL

from .response import QUploadedFile
from .response import QUploadedImageFile

from .interfaces import IQAssessedPart
from .interfaces import IQUploadedFile
from .interfaces import IQAssessedQuestion
from .interfaces import IQAssessedQuestionSet

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
			result = iface.__name__[2:] if not iface.__name__.startswith('IQuestion')\
					 else iface.__name__[1:]
		return result

	@classmethod
	def _ap_compute_external_class_name_from_concrete_class(cls, a_type):
		k = a_type.__name__
		ext_class_name = k[1:] if not k.startswith('Question') else k
		return ext_class_name

@interface.implementer(IInternalObjectExternalizer)
class _QAssessedObjectExternalizer(object):

	interface = None
	def __init__(self, assessed):
		self.assessed = assessed

	def toExternalObject(self, **kwargs):
		if hasattr(self.assessed, 'sublocations'):
			## the sublocations method for asseed parts/questions/questionsets
			## sets the full parent lineage for these objects. 
			## we wrapp the execution of it in a tuple in case it
			## returns a generator
			tuple(self.assessed.sublocations())
		return InterfaceObjectIO(self.assessed, self.interface).toExternalObject( **kwargs)

@component.adapter(IQAssessedPart)	
class _QAssessedPartExternalizer(_QAssessedObjectExternalizer):
	interface = IQAssessedPart
	
@component.adapter(IQAssessedQuestion)	
class _QAssessedQuestionExternalizer(_QAssessedObjectExternalizer):
	interface = IQAssessedQuestion

@component.adapter(IQAssessedQuestionSet)	
class _QAssessedQuestionSetExternalizer(_QAssessedObjectExternalizer):
	interface = IQAssessedQuestionSet
	
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
		updated = super(_QUploadedFileObjectIO,self).updateFromExternalObject( parsed, *args, **kwargs )
		ext_self = self._ext_replacement()
		url = parsed.get( 'url' ) or parsed.get('value')
		if url:
			data_url = DataURI(__name__='url').fromUnicode( url )
			ext_self.contentType = data_url.mimeType
			ext_self.data = data_url.data
			updated = True
		if 'filename' in parsed:
			ext_self.filename = parsed['filename']
			# some times we get full paths
			name = nameFinder( ext_self )
			if name:
				ext_self.filename = name
			updated = True
		if 'FileMimeType' in parsed:
			ext_self.contentType = bytes(parsed['FileMimeType'])
			updated = True
		return updated

	def toExternalObject( self, mergeFrom=None, **kwargs ):
		ext_dict = super(_QUploadedFileObjectIO,self).toExternalObject(**kwargs)

		# TODO: View name. Coupled to the app layer. And this is now in three
		# places.
		# It's not quite possible to fully traverse to the file sometimes
		# (TODO: verify this in this case)
		# so we go directly to the file address
		the_file = self._ext_replacement()
		ext_dict['FileMimeType'] = the_file.mimeType or None
		ext_dict['filename'] = the_file.filename or None
		ext_dict['MimeType'] = 'application/vnd.nextthought.assessment.uploadedfile'
		# We should probably register an externalizer on
		# i
		target = to_external_ntiid_oid( the_file, add_to_connection=True )
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
	url = ext_obj.get( 'url', ext_obj.get('value') )
	if url and url.startswith(b'data:'):
		ext_obj['url'] = DataURL(url)
		ext_obj.pop('value', None)
		if ext_obj['url'].mimeType.startswith('image/'):
			factory = QUploadedImageFile
	return factory
