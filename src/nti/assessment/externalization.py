#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Externalization for assessment objects.

$Id$
"""
from __future__ import unicode_literals, print_function, absolute_import
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope import component
from . import interfaces

from nti.externalization import interfaces as ext_interfaces
from nti.externalization.datastructures import AbstractDynamicObjectIO
from nti.externalization.externalization import to_external_object
from nti.externalization.externalization import to_external_ntiid_oid
from nti.externalization.autopackage import AutoPackageSearchingScopedInterfaceObjectIO

from nti.utils.schema import DataURI
from nti.utils.dataurl import DataURL
from zope.file.upload import nameFinder

@interface.implementer(ext_interfaces.IInternalObjectIO)
class _AssessmentInternalObjectIO(AutoPackageSearchingScopedInterfaceObjectIO):

	@classmethod
	def _ap_compute_external_class_name_from_interface_and_instance(cls, iface, impl):
		# Strip off 'IQ' if it's not 'IQuestionXYZ'
		return iface.__name__[2:] if not iface.__name__.startswith('IQuestion') else iface.__name__[1:]


	@classmethod
	def _ap_compute_external_class_name_from_concrete_class(cls, a_type):
		k = a_type.__name__
		ext_class_name = k[1:] if not k.startswith('Question') else k
		return ext_class_name

	@classmethod
	def _ap_enumerate_externalizable_root_interfaces(cls, asm_interfaces):
		return (asm_interfaces.IQPart, asm_interfaces.IQuestion, asm_interfaces.IQSolution,
				asm_interfaces.IQuestionSubmission, asm_interfaces.IQAssessedPart, asm_interfaces.IQAssessedQuestion,
				asm_interfaces.IQuestionSetSubmission, asm_interfaces.IQAssessedQuestionSet,
				asm_interfaces.IQHint, asm_interfaces.IQuestionSet)

	@classmethod
	def _ap_enumerate_module_names(cls):
		return ('hint', 'assessed', 'parts', 'question', 'response', 'solution', 'submission')

_AssessmentInternalObjectIO.__class_init__()

##
# File uploads
# TODO: This can probably be generalized.
# We do want to have specific interfaces for files
# submitted for assessment reasons.
##

@component.adapter(interfaces.IQUploadedFile)
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
		url = parsed.get( 'url', parsed.get('value') )
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

		return updated

	def toExternalObject( self, mergeFrom=None ):
		ext_dict = super(_QUploadedFileObjectIO,self).toExternalObject()

		# TODO: View name. Coupled to the app layer. And this is now in three
		# places.
		# It's not quite possible to fully traverse to the file sometimes
		# (TODO: verify this in this case)
		# so we go directly to the file address
		the_file = self._ext_replacement()
		ext_dict['FileMimeType'] = the_file.mimeType or None
		ext_dict['filename'] = the_file.filename or None
		# We should probably register an externalizer on
		# i
		target = to_external_ntiid_oid( the_file, add_to_connection=True )
		if target:
			link = links.Link( target=target,
							   target_mime_type=the_file.mimeType,
							   elements=('@@download',),
							   rel="data" )
			interface.alsoProvides( link, nti_interfaces.ILinkExternalHrefOnly )
			ext_dict['url'] = to_external_object( link )
		else:
			ext_dict['url'] = None

		ext_dict['value'] = ext_dict['url']
		return ext_dict

from .response import QUploadedFile
from .response import QUploadedImageFile
def _QUploadedFileFactory(ext_obj):
	factory = QUploadedFile
	url = ext_obj.get( 'url', ext_obj.get('value') )
	if url and url.startswith(b'data:'):
		ext_obj['url'] = DataURL(url)
		ext_obj.pop('value', None)
		if ext_obj['url'].mimeType.startswith('image/'):
			factory = QUploadedImageFile
	return factory
